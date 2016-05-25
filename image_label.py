from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from bbox import BoundingBox


class ImageLabel(QLabel):
    signal_bbox_added = pyqtSignal(BoundingBox)
    signal_bbox_deleted = pyqtSignal(int)

    def __init__(self, *args):
        self.start_pt = None
        self.end_pt = None
        self.cursor_pos = None
        self.mouse_down = False
        self.show_reticle = False
        self.bboxes = []
        self.bbox_label = None
        super(ImageLabel, self).__init__(*args)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.installEventFilter(self)

    def set_bboxes(self, bboxes):
        self.bboxes = bboxes

    def clear_bboxes(self):
        self.bboxes = []

    def pt2rect(self, pt1, pt2):
        left = min(pt1.x(), pt2.x())
        top = min(pt1.y(), pt2.y())
        right = max(pt1.x(), pt2.x())
        bottom = max(pt1.y(), pt2.y())
        return QRect(left, top, right - left, bottom - top)

    def proj_bbox_to_image(self, bbox):
        roi_bbox = bbox.intersected(self.img_region).translated(
            -self.img_region.topLeft())
        return roi_bbox.scaled(self.scale_ratio)

    def draw_bbox(self, painter, bbox):
        painter.drawRect(bbox)
        painter.drawText(QPoint(bbox.x(), bbox.y() - 3), bbox.label)

    def draw_reticle(self, painter, point):
        painter.drawLine(0, point.y(), self.width(), point.y())
        painter.drawLine(point.x(), 0, point.x(), self.height())

    def paintEvent(self, event):
        super(ImageLabel, self).paintEvent(event)
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for i in range(len(self.bboxes)):
            bbox = self.bboxes[i]
            self.draw_bbox(painter, bbox)
        if not self.mouse_down:
            if self.cursor_pos is not None and self.show_reticle:
                self.draw_reticle(painter, self.cursor_pos)
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
        if event.button() == Qt.LeftButton:
            if self.bbox_label is not None:
                self.end_pt = event.pos()
                rect = self.pt2rect(self.start_pt, self.end_pt)
                if rect.width() > 4 and rect.height() > 4:
                    bbox = BoundingBox(self.bbox_label, 'manual', rect=rect)
                    self.bboxes.append(bbox)
                    self.signal_bbox_added.emit(self.proj_bbox_to_image(bbox))
            self.update()
        elif event.button() == Qt.RightButton:
            if not self.mouse_down:
                for i, bbox in enumerate(self.bboxes):
                    if bbox.contains(event.pos()):
                        self.bboxes.pop(i)
                        self.signal_bbox_deleted.emit(i)
                self.update()
        self.show_reticle = False
        self.mouse_down = False

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        if self.show_reticle or self.mouse_down:
            self.update()

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_V and not self.mouse_down:
                self.show_reticle = not self.show_reticle
                self.update()
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
    def update_bboxes(self, bboxes):
        self.clear_bboxes()
        for bbox in bboxes:
            bbox_show = bbox.scaled(1 / self.scale_ratio).translated(
                self.img_region.topLeft())
            self.bboxes.append(bbox_show)

    @pyqtSlot(str)
    def update_bbox_label(self, label):
        self.bbox_label = label
