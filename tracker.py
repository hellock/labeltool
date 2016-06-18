import dlib

from bbox import BoundingBox


class Tracker(dlib.correlation_tracker):

    def __init__(self):
        self.label = None
        super(Tracker, self).__init__()

    def start_track(self, frame, bbox):
        self.label = bbox.label
        super(Tracker, self).start_track(
            frame.raw_img,
            dlib.rectangle(bbox.left(), bbox.top(), bbox.right(), bbox.bottom())
        )

    def update(self, frame):
        super(Tracker, self).update(frame.raw_img)
        rect = super(Tracker, self).get_position()
        l = int(rect.left())
        r = int(rect.right())
        t = int(rect.top())
        b = int(rect.bottom())
        return BoundingBox(self.label, l, t, r - l, b - t)
