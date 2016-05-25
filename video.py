import json
import os
import threading
import time
from collections import OrderedDict
from enum import Enum

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QObject, QRect, pyqtSignal, pyqtSlot

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

    def __init__(self, img, idx):
        qimage = self.mat2qimage(img)
        super(VideoFrame, self).__init__(QPixmap.fromImage(qimage))
        self.idx = idx

    def mat2qimage(self, img):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, depth = rgb_img.shape
        bytes_per_line = depth * width
        qimage = QImage(rgb_img.data, width, height, bytes_per_line,
                        QImage.Format_RGB888)
        return qimage

    def get_idx(self):
        return self.idx


class Annotation(object):

    def __init__(self, filename=None):
        self.data = dict(sections=[], objects={})
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        with open(filename, 'r') as fin:
            self.data = json.load(fin)
        if 'objects' not in self.data:
            self.data['objects'] = OrderedDict()

    def save(self, filename=None):
        outfile = self.filename if filename is None else filename
        with open(outfile, 'w') as fout:
            json.dump(self.data, fout, indent=4)

    def sections(self):
        return self.data['sections']

    def objects(self):
        return self.data['objects']

    def clear_bbox(self, frame_idx):
        self.data['objects'][str(frame_idx)] = []

    def add_bbox(self, frame_idx, bbox):
        if str(frame_idx) not in self.data['objects']:
            self.data['objects'][str(frame_idx)] = []
        self.data['objects'][str(frame_idx)].append(
            dict(bbox=bbox.to_list(), label=bbox.label, mode=bbox.mode))

    def del_bbox(self, frame_idx, bbox_idx):
        self.data['objects'][str(frame_idx)].pop(bbox_idx)

    def add_bboxes(self, frame_idx, bboxes):
        self.clear_bbox(frame_idx)
        for bbox in bboxes:
            self.add_bbox(frame_idx, bbox)

    def get_bboxes(self, frame_idx):
        bboxes = []
        if str(frame_idx) in self.data['objects']:
            annotation = self.data['objects'][str(frame_idx)]
            for item in annotation:
                bbox = BoundingBox(item['label'], item['mode'], *item['bbox'])
                bboxes.append(bbox)
        return bboxes


class Video(QObject):

    signal_frame_updated = pyqtSignal(VideoFrame, list)
    signal_export_progress = pyqtSignal(int)

    def __init__(self, filename=None, max_buf_size=500, max_fps=0):
        super(Video, self).__init__()
        self.cap = cv2.VideoCapture()
        self.sections = None
        self.section_idx = 0
        self.status = VideoStatus.not_loaded
        self.frame_cursor = -1
        self.frame_buf = OrderedDict()
        self.max_buf_size = max_buf_size
        self.max_fps = max_fps
        self.trackers = []
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
        if os.path.isfile(filename + '.annotation'):
            self.annotation.load(filename + '.annotation')
            self.sections = self.annotation.sections()
        else:
            self.sections = [[0, self.frame_num - 1]]
        self.section_idx = 0

    def export(self, filename):
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(filename, fourcc, self.fps,
                                 (self.frame_width, self.frame_height))
        cap = cv2.VideoCapture(self.filename)
        frame_idx = 0
        line_thickness = int(min(self.frame_width, self.frame_height) / 200)
        while cap.isOpened():
            ret, img = cap.read()
            if ret != 0:
                bboxes = self.annotation.get_bboxes(frame_idx)
                for bbox in bboxes:
                    cv2.rectangle(img, (bbox.left(), bbox.top()),
                                  (bbox.right(), bbox.bottom()), (0, 0, 255),
                                  line_thickness)
                    cv2.putText(img, bbox.label, (bbox.x(), bbox.y()),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255),
                                line_thickness)
                writer.write(img)
                frame_idx += 1
                progress = int(round(100 * frame_idx / self.frame_num))
                self.signal_export_progress.emit(progress)
            else:
                break
        cap.release()
        writer.release()

    def section_start(self):
        return self.sections[self.section_idx][0]

    def section_end(self):
        return self.sections[self.section_idx][1]

    def add2buf(self, cursor, img):
        if cursor in self.frame_buf:
            return
        if len(self.frame_buf) >= self.max_buf_size:
            self.frame_buf.popitem(last=False)
        self.frame_buf[cursor] = img

    def frame_forward(self):
        if self.frame_cursor >= self.section_end():
            self.status = VideoStatus.pause
            return
        self.frame_cursor += 1
        if self.status != VideoStatus.play_forward:
            self.status = VideoStatus.frame_forward
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            ret, img = self.cap.read()
            if ret == 0:
                return
            else:
                self.add2buf(self.frame_cursor, img)
        if len(self.trackers) == 0:
            bboxes = self.annotation.get_bboxes(self.frame_cursor)
        else:
            bboxes = self.track(img)
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       bboxes)

    def frame_backward(self):
        if self.frame_cursor <= self.section_start():
            self.status = VideoStatus.pause
            return
        self.frame_cursor -= 1
        if self.status != VideoStatus.play_backward:
            self.status = VideoStatus.frame_backward
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor)
            ret, img = self.cap.read()
            if ret == 0:
                return
            else:
                self.add2buf(self.frame_cursor, img)
        bboxes = self.annotation.get_bboxes(self.frame_cursor)
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       bboxes)

    def jump_to_frame(self, cursor):
        self.status = VideoStatus.pause
        if cursor < 0 or cursor >= self.frame_num:
            return
        self.frame_cursor = cursor
        if cursor < self.section_start() or cursor > self.section_end():
            for idx, section in enumerate(self.sections):
                if cursor <= section[1]:
                    self.section_idx = idx
                    break
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor)
            ret, img = self.cap.read()
            if ret == 0:
                return
            else:
                self.add2buf(self.frame_cursor, img)
        bboxes = self.annotation.get_bboxes(self.frame_cursor)
        self.clear_trackers()
        self.signal_frame_updated.emit(VideoFrame(img, self.frame_cursor),
                                       bboxes)

    def jump_to_section(self, section_idx):
        self.section_idx = section_idx
        self.jump_to_frame(self.section_start())
        self.annotation.save()

    def jump_to_next_section(self):
        if self.section_idx < len(self.sections) - 1:
            self.section_idx += 1
            self.jump_to_section(self.section_idx)

    def play_forward(self):
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_forward and
               self.frame_cursor < self.section_end()):
            start = time.time()
            self.frame_forward()
            ellapsed = time.time() - start
            if self.max_fps > 0 and ellapsed < min_interval:
                time.sleep(min_interval - ellapsed)

    def play_backward(self):
        min_interval = 1 / self.max_fps if self.max_fps > 0 else 0
        while (self.status == VideoStatus.play_backward and
               self.frame_cursor > self.section_start()):
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
        bboxes = []
        frame_rect = QRect(0, 0, self.frame_width, self.frame_height)
        for tracker in self.trackers:
            bbox = tracker.update(img).intersected(frame_rect)
            bboxes.append(bbox)
        self.annotation.add_bboxes(self.frame_cursor, bboxes)
        return bboxes

    def add_trackers(self, bboxes):
        for bbox in bboxes:
            self.add_tracker(bbox)

    def clear_trackers(self):
        self.trackers = []

    @pyqtSlot(BoundingBox)
    def add_tracker(self, bbox):
        tracker = Tracker()
        tracker.start_track(self.frame_buf[self.frame_cursor], bbox)
        self.trackers.append(tracker)
        self.annotation.add_bbox(self.frame_cursor, bbox)

    @pyqtSlot(int)
    def del_tracker(self, idx):
        if len(self.trackers) > idx:
            self.trackers.pop(idx)
        self.annotation.del_bbox(self.frame_cursor, idx)
