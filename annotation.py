import json
import os
# from collections import defaultdict

from bbox import BoundingBox


class Tube(object):

    def __init__(self, id, label, start, end=0, bboxes=[]):
        self.id = id
        self.label = label
        self.start = start
        self.end = start if end == 0 else end
        self.bboxes = bboxes

    def set_bbox(self, frame_id, bbox):
        while len(self.bboxes) < frame_id - self.start + 1:
            self.bboxes.append([])
        self.bboxes[frame_id - self.start] = bbox
        if self.end < frame_id:
            self.end = frame_id

    def get_bbox(self, frame_id):
        if frame_id >= self.start and frame_id <= self.end:
            return self.bboxes[frame_id - self.start]
        else:
            return None

    def del_later_bboxes(self, frame_id):
        for i in range(self.start + len(self.bboxes) - frame_id):
            self.bboxes.pop()
        self.end = frame_id - 1

    def set_end(self, end):
        self.end = end

    def brief_info(self):
        return [self.id, self.label, self.start, self.end]

    def to_dict(self):
        return dict(label=self.label, start=self.start, end=self.end,
                    bboxes=self.bboxes)


class Annotation(object):

    def __init__(self, filename=None):
        self.tubes = dict()
        self.next_tube_id = 1
        # self.data = dict(tubes=dict())
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as fin:
            self.data = json.load(fin)
        if 'tubes' in self.data:
            for tube_id_str, tube in self.data['tubes'].items():
                tube_id = int(tube_id_str)
                self.tubes[tube_id] = Tube(
                    tube_id, tube['label'], tube['start'],
                    tube['end'], tube['bboxes'])
                if self.next_tube_id <= tube_id:
                    self.next_tube_id = tube_id + 1

    def save(self, filename=None):
        outfile = self.filename if filename is None else filename
        self.data = dict(tubes=dict())
        for tube_id, tube in self.tubes.items():
            self.data['tubes'][tube_id] = tube.to_dict()
        with open(outfile, 'w') as fout:
            json.dump(self.data, fout)

    def tube(self, tube_id):
        if tube_id in self.tubes:
            return self.tubes[tube_id]
        else:
            return None

    def add_tube(self, label, start):
        self.tubes[self.next_tube_id] = Tube(self.next_tube_id, label, start)
        self.next_tube_id += 1

    def set_bbox(self, tube_id, frame_id, bbox):
        if isinstance(bbox, BoundingBox):
            bbox = bbox.to_list()
        self.tubes[tube_id].set_bbox(frame_id, bbox)

    def del_later_bboxes(self, tube_id, frame_id):
        self.tubes[tube_id].del_later_bboxes(frame_id)

    def get_bbox(self, tube_id, frame_id):
        if tube_id in self.tubes:
            bbox = self.tubes[tube_id].get_bbox(frame_id)
            if bbox is not None:
                return BoundingBox(self.tubes[tube_id].label, *bbox)
            else:
                return None

    def get_bboxes(self, frame_id, ignore_tube_id=None):
        bboxes = []
        for tube_id, tube in self.tubes.items():
            if tube_id == ignore_tube_id:
                continue
            bbox = tube.get_bbox(frame_id)
            if bbox is not None:
                bboxes.append(BoundingBox(tube.label, *bbox))
        return bboxes

    def get_brief_info(self):
        info = []
        for tube in self.tubes.values():
            info.append(tube.brief_info())
        return info
