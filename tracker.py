import dlib

from bbox import BoundingBox


class Tracker(dlib.correlation_tracker):

    def __init__(self):
        self.label = None
        self.init_region = None
        self.bbox = None
        self.track_num = 0
        super(Tracker, self).__init__()

    def start_track(self, frame, bbox):
        self.bbox = bbox
        self.init_region = frame.raw_img[bbox.left: bbox.right,
                                         bbox.top: bbox.bottom]
        self.label = bbox.label
        super(Tracker, self).start_track(
            frame.raw_img,
            dlib.rectangle(bbox.left, bbox.top, bbox.right, bbox.bottom)
        )

    def update(self, frame):
        self.track_num += 1
        score = super(Tracker, self).update(frame.raw_img)
        rect = super(Tracker, self).get_position()
        l = int(rect.left())
        r = int(rect.right())
        t = int(rect.top())
        b = int(rect.bottom())
        self.bbox = BoundingBox(self.label, 0, l, t, r - l, b - t)
        return (self.bbox, score)
