import time
import threading

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Video(QObject):

    signal_frame_updated = pyqtSignal(bool, QPixmap, name='frameUpdated')

    def __init__(self, filepath, max_buf_size):
        super(Video, self).__init__()
        self.filepath = filepath
        self.cap = cv2.VideoCapture(filepath)
        self.frame_buf = {}
        self.frame_buf_order = []
        self.max_buf_size = max_buf_size
        self.frame_cursor = -1
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(round(self.cap.get(cv2.CAP_PROP_FPS)))
        self.frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.play_status = 0

    def mat2qpixmap(self, img):
        tmp_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, depth = tmp_img.shape
        bytes_per_line = depth * width
        qt_img = QImage(tmp_img.data, width, height, bytes_per_line,
                        QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        return pixmap

    def add2buf(self, cursor, img):
        if cursor in self.frame_buf:
            return
        if len(self.frame_buf) >= self.max_buf_size:
            earlist = self.frame_buf_order[0]
            del self.frame_buf[earlist]
            del self.frame_buf_order[0]
        self.frame_buf[cursor] = img
        self.frame_buf_order.append(cursor)

    def next_frame(self):
        if self.frame_cursor < self.frame_num - 1:
            self.frame_cursor += 1
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            # start = time.time()
            ret, img = self.cap.read()
            # tmp = time.time()
            # read_time = tmp - start
            if ret == 0:
                self.signal_frame_updated.emit(False, QPixmap())
                return
            else:
                self.add2buf(self.frame_cursor, img)
        self.signal_frame_updated.emit(True, self.mat2qpixmap(img))

    def last_frame(self):
        if self.frame_cursor > 0:
            self.frame_cursor -= 1
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor)
            ret, img = self.cap.read()
            if ret == 0:
                self.signal_frame_updated.emit(False, QPixmap())
                return
            else:
                self.add2buf(self.frame_cursor, img)
        self.signal_frame_updated.emit(True, self.mat2qpixmap(img))

    def set_pos(self, cursor):
        self.frame_cursor = cursor
        if self.frame_cursor in self.frame_buf:
            img = self.frame_buf[self.frame_cursor]
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_cursor)
            ret, img = self.cap.read()
            if ret == 0:
                self.signal_frame_updated.emit(False, QPixmap())
                return
            else:
                self.add2buf(self.frame_cursor, img)
        self.signal_frame_updated.emit(True, self.mat2qpixmap(img))

    def play_forward(self):
        while self.play_status == 1 and self.frame_cursor < self.frame_num - 1:
            self.next_frame()
            time.sleep(0.01)

    def play_backward(self):
        while self.play_status == -1 and self.frame_cursor > 0:
            self.last_frame()
            time.sleep(0.01)

    @pyqtSlot(int)
    def play_ctl(self, status):
        self.play_status = status
        if self.play_status == 1:
            t = threading.Thread(target=self.play_forward)
            t.daemon = True
            t.start()
        elif self.play_status == -1:
            t = threading.Thread(target=self.play_backward)
            t.daemon = True
            t.start()
