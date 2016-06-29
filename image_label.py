from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from bbox import BoundingBox


class ImageLabel(QLabel):
    bbox_added = pyqtSignal(BoundingBox)
    bbox_deleted = pyqtSignal()

    def __init__(self, *args):
        super(ImageLabel, self).__init__(*args)
        self.start_pt = None
        self.end_pt = None
        self.cursor_pos = None
        self.mouse_down = False
        self.show_reticle = False
        self.bbox_label = None
        self.clear_bboxes()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.installEventFilter(self)

    def clear_bboxes(self):
        self.bboxes = dict(current_tube=None, other_tubes=[])

    def update_bbox_label(self, label):
        self.bbox_label = label

    def pt2rect(self, pt1, pt2):
        left = int(min(pt1.x(), pt2.x()))
        top = int(min(pt1.y(), pt2.y()))
        right = int(max(pt1.x(), pt2.x()))
        bottom = int(max(pt1.y(), pt2.y()))
        return QRect(left, top, right - left + 1, bottom - top + 1)

    def proj_to_real_img(self, bbox):
        roi_bbox = bbox.intersected(self.img_region)
        roi_bbox.shift(-self.img_region.x, -self.img_region.y)
        roi_bbox.scale(self.scale_ratio)
        return roi_bbox

    def proj_to_image_label(self, bbox):
        show_bbox = bbox.scaled(1 / self.scale_ratio)
        show_bbox.shift(self.img_region.x, self.img_region.y)
        return show_bbox

    def draw_bbox(self, painter, bbox):
        painter.drawRect(bbox.to_qrect())
        painter.drawText(QPoint(bbox.x, bbox.y - 3), bbox.label)

    def draw_reticle(self, painter, point):
        painter.drawLine(0, point.y(), self.width(), point.y())
        painter.drawLine(point.x(), 0, point.x(), self.height())

    def paintEvent(self, event):
        super(ImageLabel, self).paintEvent(event)
        painter = QPainter()
        painter.begin(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for bbox in self.bboxes['other_tubes']:
            self.draw_bbox(painter, bbox)
        painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        if self.bboxes['current_tube'] is not None:
            self.draw_bbox(painter, self.bboxes['current_tube'])
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
                if rect.width() > 5 and rect.height() > 5:
                    bbox = BoundingBox.from_qrect(rect, self.bbox_label, 1)
                    self.bboxes['current_tube'] = bbox
                    self.bbox_added.emit(self.proj_to_real_img(bbox))
            self.update()
        elif event.button() == Qt.RightButton:
            if not self.mouse_down:
                bbox = self.bboxes['current_tube']
                if (bbox is not None and
                        bbox.contain(event.pos().x(), event.pos().y())):
                    self.bboxes['current_tube'] = None
                    self.bbox_deleted.emit()
                self.update()
        self.mouse_down = False

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.pos()
        if self.show_reticle or self.mouse_down:
            self.update()

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_V and not self.mouse_down:
                self.toggle_reticle()
                return True
        return False

    def toggle_reticle(self, force_show=False):
        if force_show:
            self.show_reticle = True
        else:
            self.show_reticle = not self.show_reticle
        self.update()

    def display(self, pixmap):
        self.scale_ratio = max(pixmap.width() / self.width(),
                               pixmap.height() / self.height())
        scaled_pixmap = pixmap.scaled(self.width() - 2, self.height() - 2,
                                      Qt.KeepAspectRatio)
        x = int((self.width() - scaled_pixmap.width()) / 2)
        y = int((self.height() - scaled_pixmap.height()) / 2)
        self.img_region = BoundingBox.from_qrect(
            QRect(QPoint(x, y), scaled_pixmap.size()))
        self.setPixmap(scaled_pixmap)
        self.update()

    def update_bboxes(self, bboxes):
        self.clear_bboxes()
        if bboxes['current_tube'] is not None:
            self.bboxes['current_tube'] = self.proj_to_image_label(
                bboxes['current_tube'])
        for bbox in bboxes['other_tubes']:
            self.bboxes['other_tubes'].append(
                self.proj_to_image_label(bbox))
