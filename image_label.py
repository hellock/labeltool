from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ImageLabel(QLabel):
    signal_rect_added = pyqtSignal(QRect)
    signal_rect_deleted = pyqtSignal(int)

    def __init__(self, *args):
        self.start_pt = None
        self.end_pt = None
        self.cursor_pos = None
        self.mouse_down = False
        self.show_reticle = False
        self.rects = []
        self.bbox_labels = []
        self.bbox_label = None
        super(ImageLabel, self).__init__(*args)
        self.setMouseTracking(True)
        self.installEventFilter(self)

    def set_rects(self, rects):
        self.rects = rects

    def pt2rect(self, pt1, pt2):
        left = min(pt1.x(), pt2.x())
        top = min(pt1.y(), pt2.y())
        right = max(pt1.x(), pt2.x())
        bottom = max(pt1.y(), pt2.y())
        return QRect(left, top, right - left, bottom - top)

    def scale_rect(self, rect, scale_ratio):
        new_x = int(rect.x() * scale_ratio)
        new_y = int(rect.y() * scale_ratio)
        new_w = int(rect.width() * scale_ratio)
        new_h = int(rect.height() * scale_ratio)
        return QRect(new_x, new_y, new_w, new_h)

    def proj_rect_to_image(self, rect):
        roi_rect = self.img_region.intersected(rect).translated(
            -self.img_region.topLeft())
        return self.scale_rect(roi_rect, self.scale_ratio)

    def paintEvent(self, event):
        super(ImageLabel, self).paintEvent(event)
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for i in range(len(self.rects)):
            rect = self.rects[i]
            painter.drawRect(rect)
            painter.drawText(QPoint(rect.x(), rect.y() - 3), self.bbox_labels[i])
        if not self.mouse_down:
            pos = self.cursor_pos
            if pos is not None and self.show_reticle:
                painter.drawLine(0, pos.y(), self.width(), pos.y())
                painter.drawLine(pos.x(), 0, pos.x(), self.height())
        else:
            painter.drawRect(self.pt2rect(self.start_pt, self.cursor_pos))
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.show_reticle:
            self.start_pt = event.pos()
            self.mouse_down = True

    def mouseReleaseEvent(self, event):
        if not self.show_reticle and event.button() == Qt.LeftButton:
            return
        self.mouse_down = False
        self.show_reticle = False
        if event.button() == Qt.LeftButton:
            self.end_pt = event.pos()
            rect = self.pt2rect(self.start_pt, self.end_pt)
            self.rects.append(rect)
            self.bbox_labels.append(self.bbox_label)
            self.signal_rect_added.emit(self.proj_rect_to_image(rect))
            self.update()
        elif event.button() == Qt.RightButton:
            for i in range(len(self.rects)):
                if self.rects[i].contains(event.pos()):
                    self.rects.pop(i)
                    self.bbox_labels.pop(i)
                    self.signal_rect_deleted.emit(i)
                    self.update()

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        if self.show_reticle or self.mouse_down:
            self.update()

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            print(event.key())
            if event.key() == Qt.Key_Control:
                self.show_reticle = not self.show_reticle
                return True
        return False

    def show_img(self, pixmap):
        self.scale_ratio = max(pixmap.width() / self.width(),
                               pixmap.height() / self.height())
        scaled_pixmap = pixmap.scaled(self.width() - 2, self.height() - 2,
                                      Qt.KeepAspectRatio)
        x = int((self.width() - scaled_pixmap.width()) / 2)
        y = int((self.height() - scaled_pixmap.height()) / 2)
        self.img_region = QRect(QPoint(x, y), scaled_pixmap.size())
        self.setPixmap(scaled_pixmap)
        self.update()

    @pyqtSlot(list)
    def update_rects(self, rects):
        self.rects = []
        for rect in rects:
            show_rect = self.scale_rect(rect, 1 / self.scale_ratio).translated(
                self.img_region.topLeft())
            self.rects.append(show_rect)

    @pyqtSlot(str)
    def update_bbox_label(self, label):
        self.bbox_label = label
