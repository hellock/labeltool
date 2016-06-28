from ckutils.rect import Rect


class BoundingBox(Rect):

    def __init__(self, label=None, src=0, *args, **kwargs):
        self.label = label
        self.src = src
        super(BoundingBox, self).__init__(*args, **kwargs)

    @staticmethod
    def from_qrect(qrect, label=None, src=0):
        return BoundingBox(label, src, qrect.x(), qrect.y(),
                           qrect.width(), qrect.height())

    def copy(self):
        return BoundingBox(self.label, self.src, *list(self))
