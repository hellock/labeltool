from PyQt5.QtCore import QRect


class BoundingBox(QRect):

    def __init__(self, label=None, *args, **kwargs):
        self.label = label
        if 'rect' in kwargs:
            super(BoundingBox, self).__init__(kwargs['rect'].topLeft(),
                                              kwargs['rect'].size())
        else:
            super(BoundingBox, self).__init__(*args, **kwargs)

    def intersected(self, rect):
        inter_rect = super(BoundingBox, self).intersected(rect)
        return BoundingBox(self.label, rect=inter_rect)

    def translated(self, pt):
        rect = super(BoundingBox, self).translated(pt)
        return BoundingBox(self.label, rect=rect)

    def scaled(self, scale_ratio):
        new_x = int(self.x() * scale_ratio)
        new_y = int(self.y() * scale_ratio)
        new_w = int(self.width() * scale_ratio)
        new_h = int(self.height() * scale_ratio)
        return BoundingBox(self.label, new_x, new_y, new_w, new_h)

    def to_list(self, type='xywh'):
        if type == 'xywh':
            return [self.x(), self.y(), self.width(), self.height()]
        elif type == 'ltrb':
            return [self.x(), self.y(), self.right(), self.bottom()]
        else:
            return []
