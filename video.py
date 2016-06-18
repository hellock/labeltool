import threading
import time
from collections import OrderedDict
from enum import Enum

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QObject, QRect, pyqtSignal

from ckutils import VideoUtil


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
        self.raw_img = img

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

    frame_updated = pyqtSignal(VideoFrame)
    export_progress_updated = pyqtSignal(int)

    def __init__(self, filename=None, max_buf_size=500, max_fps=0):
        super(Video, self).__init__()
        self.vreader = None
        self.video_buffer = VideoBuffer(max_buf_size)
        self.status = VideoStatus.not_loaded
        self.cursor = 0
        self.max_fps = max_fps
        self.filename = filename
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        self.vreader = cv2.VideoCapture(filename)
        self.status = VideoStatus.pause
        self.width = int(self.vreader.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vreader.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(round(self.vreader.get(cv2.CAP_PROP_FPS)))
        self.frame_cnt = int(self.vreader.get(cv2.CAP_PROP_FRAME_COUNT))

    def get_frame(self, frame_id=0):
        """get a frame by frame_id
        frame_id = 0 means the next frame
        """
        self.cursor = frame_id
        img = self.video_buffer.get(self.cursor)
        if img is None:
            if frame_id > 0:
                self.vreader.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)
                VideoUtil.check_pos(self.vreader, frame_id - 1)
            ret, img = self.vreader.read()
            if ret == 0:
                return None
            self.video_buffer.put(self.cursor, img)
        return VideoFrame(img, self.cursor)

    def current_frame(self):
        img = self.video_buffer.get(self.cursor)
        return VideoFrame(img, self.cursor)

    def frame_forward(self):
        if self.cursor >= self.frame_cnt:
            self.status = VideoStatus.pause
            return
        if self.status != VideoStatus.play_forward:
            self.status = VideoStatus.frame_forward
        return self.get_frame(self.cursor + 1)

    def frame_backward(self):
        if self.cursor <= 1:
            self.status = VideoStatus.pause
            return
        if self.status != VideoStatus.play_backward:
            self.status = VideoStatus.frame_backward
        return self.get_frame(self.cursor - 1)

    def jump_to_frame(self, frame_id):
        self.status = VideoStatus.pause
        if frame_id < 1 or frame_id > self.frame_cnt:
            return
        return self.get_frame(frame_id)

    def play_forward_func(self):
        self.status = VideoStatus.play_forward
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_forward and
               self.cursor < self.frame_cnt):
            start = time.time()
            frame = self.frame_forward()
            ellapsed = time.time() - start
            if self.max_fps > 0 and ellapsed < min_interval:
                time.sleep(min_interval - ellapsed)
            self.frame_updated.emit(frame)

    def play_backward_func(self):
        self.status = VideoStatus.play_backward
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_backward and self.cursor > 1):
            start = time.time()
            frame = self.frame_backward()
            ellapsed = time.time() - start
            if self.max_fps > 0 and ellapsed < min_interval:
                time.sleep(min_interval - ellapsed)
            self.frame_updated.emit(frame)

    def play_forward(self):
        t = threading.Thread(target=self.play_forward_func)
        t.daemon = True
        t.start()

    def play_backward(self):
        t = threading.Thread(target=self.play_backward_func)
        t.daemon = True
        t.start()

    def pause(self):
        self.status = VideoStatus.pause

    def is_forward(self):
        if (self.status == VideoStatus.play_forward or
                self.status == VideoStatus.frame_forward):
            return True
        else:
            return False

    def track(self, img):
        frame_rect = QRect(0, 0, self.width, self.height)
        bbox = self.tracker.update(img).intersected(frame_rect)
        return bbox

    def export(self, out_file, annotation, start=1, end=0):
        completed = 0
        end = self.frame_cnt if end == 0 else end
        export_num = end - start + 1
        line_thickness = int(min(self.width, self.height) / 200)
        vreader = cv2.VideoCapture(self.filename)
        vreader.set(cv2.CAP_PROP_POS_FRAMES, start - 1)
        VideoUtil.check_pos(start - 1)
        vwriter = cv2.VideoWriter(out_file, cv2.VideoWriter_fourcc(*'XVID'),
                                  self.fps, (self.width, self.height))
        while vreader.isOpened() and completed < export_num:
            ret, img = vreader.read()
            if ret == 0:
                break
            bboxes = annotation.get_bboxes(completed + start)
            for bbox in bboxes:
                cv2.rectangle(img, (bbox.left(), bbox.top()),
                              (bbox.right(), bbox.bottom()), (0, 0, 255),
                              line_thickness)
                cv2.putText(img, bbox.label, (bbox.x(), bbox.y()),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255),
                            line_thickness)
            vwriter.write(img)
            completed += 1
            progress = int(round(100 * completed / export_num))
            self.export_progress_updated.emit(progress)
        vreader.release()
        vwriter.release()
