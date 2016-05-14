from PyQt5.QtCore import QRect


class BoundingBox(QRect):

    def __init__(self, label=None, mode='manual', *args, **kwargs):
        self.label = label
        self.mode = mode
        if 'rect' in kwargs:
            super(BoundingBox, self).__init__(kwargs['rect'].topLeft(),
                                              kwargs['rect'].size())
        else:
            super(BoundingBox, self).__init__(*args, **kwargs)

    def intersected(self, rect):
        inter_rect = super(BoundingBox, self).intersected(rect)
        return BoundingBox(self.label, self.mode, rect=inter_rect)

    def translated(self, pt):
        rect = super(BoundingBox, self).translated(pt)
        return BoundingBox(self.label, self.mode, rect=rect)

    def scaled(self, scale_ratio):
        new_x = int(self.x() * scale_ratio)
        new_y = int(self.y() * scale_ratio)
        new_w = int(self.width() * scale_ratio)
        new_h = int(self.height() * scale_ratio)
        return BoundingBox(self.label, self.mode,
                           new_x, new_y, new_w, new_h)

    def to_list(self):
        return [self.x(), self.y(), self.width(), self.height()]