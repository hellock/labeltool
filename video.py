import threading
import time
from collections import OrderedDict
from enum import Enum

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QObject, QRect, pyqtSignal, pyqtSlot

from annotation import Annotation
from bbox import BoundingBox
from tracker import Tracker


class VideoStatus(Enum):
    not_loaded = -1
    pause = 0
    play_forward = 1
    play_backward = 2
    frame_forward = 3
    frame_backward = 4


class VideoFrame(QPixmap):

    def __init__(self, img, id):
        qimage = self.mat2qimage(img)
        super(VideoFrame, self).__init__(QPixmap.fromImage(qimage))
        self.id = id

    def mat2qimage(self, img):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, depth = rgb_img.shape
        bytes_per_line = depth * width
        qimage = QImage(rgb_img.data, width, height, bytes_per_line,
                        QImage.Format_RGB888)
        return qimage


class VideoBuffer(object):

    def __init__(self, max_size):
        self.buf = OrderedDict()
        self.max_size = max_size

    def put(self, frame_id, img):
        if frame_id in self.buf:
            return
        if len(self.buf) >= self.max_size:
            self.buf.popitem(last=False)
        self.buf[frame_id] = img

    def get(self, frame_id):
        if frame_id in self.buf:
            return self.buf[frame_id]
        else:
            return None


class Video(QObject):

    signal_frame_updated = pyqtSignal(VideoFrame, dict)
    signal_tube_annotated = pyqtSignal(list)
    signal_export_progress = pyqtSignal(int)

    def __init__(self, filename=None, max_buf_size=500, max_fps=0):
        super(Video, self).__init__()
        self.cap = cv2.VideoCapture()
        self.reset_tube_id()
        self.status = VideoStatus.not_loaded
        self.frame_cursor = 0
        self.video_buffer = VideoBuffer(max_buf_size)
        self.max_fps = max_fps
        self.tracker = None
        self.annotation = Annotation()
        self.filename = filename
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        self.cap = cv2.VideoCapture(filename)
        self.status = VideoStatus.pause
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(round(self.cap.get(cv2.CAP_PROP_FPS)))
        self.frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.annotation.load(filename + '.annotation')

    def export(self, filename, start=1, end=0):
        writer = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'),
                                 self.fps,
                                 (self.frame_width, self.frame_height))
        frame_idx = 0
        end = self.frame_num if end == 0 else end
        export_num = end - start + 1
        cap = cv2.VideoCapture(self.filename)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start - 1)
        line_thickness = int(min(self.frame_width, self.frame_height) / 200)
        while cap.isOpened() and frame_idx <= end:
            ret, img = cap.read()
            if ret == 0:
                break
            bboxes = self.annotation.get_bboxes(frame_idx + start)
            for bbox in bboxes:
                cv2.rectangle(img, (bbox.left(), bbox.top()),
                              (bbox.right(), bbox.bottom()), (0, 0, 255),
                              line_thickness)
                cv2.putText(img, bbox.label, (bbox.x(), bbox.y()),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255),
                            line_thickness)
            writer.write(img)
            frame_idx += 1
            progress = int(round(100 * frame_idx / export_num))
            self.signal_export_progress.emit(progress)
        cap.release()
        writer.release()

    def reset_tube_id(self):
        self.tube_id = 0

    def tube_start(self):
        return self.annotation.tube(self.tube_id).start

    def tube_end(self):
        return self.annotation.tube(self.tube_id).end

    def add_tube(self, label):
        self.tube_id = self.annotation.next_tube_id
        self.annotation.add_tube(label, self.frame_cursor)

    def frame_forward(self):
        if self.frame_cursor >= self.frame_num:
            self.status = VideoStatus.pause
            return
        self.frame_cursor += 1
        if self.status != VideoStatus.play_forward:
            self.status = VideoStatus.frame_forward
        img = self.video_buffer.get(self.frame_cursor)
        if img is None:
            ret, img = self.cap.read()
            if ret == 0:
                return
            self.video_buffer.put(self.frame_cursor, img)
        if self.tracker is not None:
            current_tube_bbox = self.track(img)
        else:
            current_tube_bbox = self.annotation.get_bbox(self.tube_id,
                                                         self.frame_cursor)
        other_tube_bboxes = self.annotation.get_bboxes(self.frame_cursor,
                                                       self.tube_id)
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       dict(current_tube=current_tube_bbox,
                                            other_tubes=other_tube_bboxes))

    def frame_backward(self):
        if self.frame_cursor <= 1:
            self.status = VideoStatus.pause
            return
        self.frame_cursor -= 1
        if self.status != VideoStatus.play_backward:
            self.status = VideoStatus.frame_backward
        img = self.video_buffer.get(self.frame_cursor)
        if img is None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor - 1)
            ret, img = self.cap.read()
            if ret == 0:
                return
            self.video_buffer.put(self.frame_cursor, img)
        current_tube_bbox = self.annotation.get_bbox(self.tube_id,
                                                     self.frame_cursor)
        other_tube_bboxes = self.annotation.get_bboxes(self.frame_cursor,
                                                       self.tube_id)
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       dict(current_tube=current_tube_bbox,
                                            other_tubes=other_tube_bboxes))

    def jump_to_frame(self, cursor):
        self.status = VideoStatus.pause
        if cursor < 1 or cursor > self.frame_num:
            return
        self.frame_cursor = cursor
        self.clear_tracker()
        img = self.video_buffer.get(self.frame_cursor)
        if img is None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor - 1)
            ret, img = self.cap.read()
            if ret == 0:
                return
            self.video_buffer.put(self.frame_cursor, img)
        current_tube_bbox = self.annotation.get_bbox(self.tube_id,
                                                     self.frame_cursor)
        other_tube_bboxes = self.annotation.get_bboxes(self.frame_cursor,
                                                       self.tube_id)
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       dict(current_tube=current_tube_bbox,
                                            other_tubes=other_tube_bboxes))

    def jump_to_tube(self, tube_id):
        self.tube_id = tube_id
        self.jump_to_frame(self.tube_start())
        self.annotation.save()

    def play_forward(self):
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_forward and
               self.frame_cursor < self.frame_num):
            start = time.time()
            self.frame_forward()
            ellapsed = time.time() - start
            if self.max_fps > 0 and ellapsed < min_interval:
                time.sleep(min_interval - ellapsed)

    def play_backward(self):
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_backward and
               self.frame_cursor > 1):
            start = time.time()
            self.frame_backward()
            ellapsed = time.time() - start
            if self.max_fps > 0 and ellapsed < min_interval:
                time.sleep(min_interval - ellapsed)

    def play_ctrl(self, status):
        self.status = status
        if self.status == VideoStatus.play_forward:
            t = threading.Thread(target=self.play_forward)
            t.daemon = True
            t.start()
        elif self.status == VideoStatus.play_backward:
            t = threading.Thread(target=self.play_backward)
            t.daemon = True
            t.start()
        elif self.status == VideoStatus.frame_forward:
            self.frame_forward()
        elif self.status == VideoStatus.frame_backward:
            self.frame_backward()

    def track(self, img):
        frame_rect = QRect(0, 0, self.frame_width, self.frame_height)
        bbox = self.tracker.update(img).intersected(frame_rect)
        self.annotation.set_bbox(self.tube_id, self.frame_cursor, bbox)
        return bbox

    def clear_tracker(self):
        self.tracker = None

    @pyqtSlot(BoundingBox)
    def set_tracker(self, bbox):
        self.tracker = Tracker()
        self.tracker.start_track(self.video_buffer.get(self.frame_cursor), bbox)
        self.annotation.set_bbox(self.tube_id, self.frame_cursor, bbox)

    @pyqtSlot()
    def del_tracker(self):
        self.clear_tracker()
        self.annotation.del_later_bboxes(self.tube_id, self.frame_cursor)
        self.annotation.save()
        tube_info = self.annotation.tube(self.tube_id).brief_info()
        self.signal_tube_annotated.emit([tube_info])
        self.reset_tube_id()
