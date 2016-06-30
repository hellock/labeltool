import json
import os

from bbox import BoundingBox


class Tube(object):

    def __init__(self, id, label, start, end=None, bboxes=[]):
        self._id = id
        self._label = label
        self._start = start
        self._end = start if end is None else end
        self.bboxes = bboxes

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        if end < self._start:
            raise ValueError('end must be greater than or equal to start')
        self._end = end

    def set_bbox(self, frame_id, bbox):
        while len(self.bboxes) < frame_id - self._start + 1:
            self.bboxes.append([])
        self.bboxes[frame_id - self._start] = bbox
        if self._end < frame_id:
            self._end = frame_id

    def get_bbox(self, frame_id):
        if frame_id >= self._start and frame_id <= self._end:
            return self.bboxes[frame_id - self._start]
        else:
            return None

    def interpolate(self, bbox, from_frame, to_frame):
        cnt = to_frame - from_frame
        if cnt <= 1:
            return
        from_bbox = self.bboxes[from_frame - self._start]
        step_x = (bbox.x - from_bbox.x) / cnt
        step_y = (bbox.y - from_bbox.y) / cnt
        step_w = (bbox.w - from_bbox.w) / cnt
        step_h = (bbox.h - from_bbox.h) / cnt
        bbox = self.bboxes[from_frame - self._start]
        for i in range(1, cnt):
            self.bboxes[from_frame - self._start + i].set(
                int(round(bbox.x + step_x * i)),
                int(round(bbox.y + step_y * i)),
                int(round(bbox.w + step_w * i)),
                int(round(bbox.h + step_h * i)))

    def del_later_bboxes(self, frame_id):
        for i in range(self._start + len(self.bboxes) - frame_id):
            self.bboxes.pop()
        self._end = frame_id - 1

    def to_dict(self, with_bboxes=True):
        tube_dict = dict(id=self._id, label=self._label,
                         start=self._start, end=self._end)
        if with_bboxes:
            tube_dict['bboxes'] = []
            for bbox in self.bboxes:
                tube_dict['bboxes'].append(
                    {'bbox': list(bbox), 'src': bbox.src})
        return tube_dict

    @staticmethod
    def from_dict(tube_dict):
        tube = Tube(tube_dict['id'], tube_dict['label'],
                    tube_dict['start'], tube_dict['end'])
        tube.bboxes = []
        if 'bboxes' in tube_dict:
            for bbox in tube_dict['bboxes']:
                tube.bboxes.append(
                    BoundingBox(tube.label, bbox['src'], *bbox['bbox']))
        return tube


class Annotation(object):

    def __init__(self, filename=None):
        self.tubes = dict()
        self.next_tube_id = 1
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.filename = filename
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as fin:
            self.data = json.load(fin)
        if 'tubes' in self.data:
            for tube_id, tube in self.data['tubes'].items():
                tube_id = int(tube_id)
                self.tubes[tube_id] = Tube.from_dict(tube)
                if self.next_tube_id <= tube_id:
                    self.next_tube_id = tube_id + 1

    def save(self, filename=None):
        out_file = self.filename if filename is None else filename
        self.data = dict(tubes=dict())
        for tube_id, tube in self.tubes.items():
            self.data['tubes'][tube_id] = tube.to_dict()
        with open(out_file, 'w') as fout:
            json.dump(self.data, fout)

    def tube(self, tube_id):
        if tube_id in self.tubes:
            return self.tubes[tube_id]
        else:
            return None

    def tube_start(self, tube_id):
        return self.tubes[tube_id].start

    def tube_end(self, tube_id):
        return self.tubes[tube_id].end

    def add_tube(self, label, start):
        self.tubes[self.next_tube_id] = Tube(self.next_tube_id, label, start)
        self.next_tube_id += 1

    def set_bbox(self, tube_id, frame_id, bbox):
        self.tubes[tube_id].set_bbox(frame_id, bbox)

    def interpolate(self, tube_id, bbox, from_frame, to_frame):
        self.tubes[tube_id].interpolate(bbox, from_frame, to_frame)

    def del_later_bboxes(self, tube_id, frame_id):
        self.tubes[tube_id].del_later_bboxes(frame_id)

    def get_bbox(self, tube_id, frame_id):
        if tube_id not in self.tubes:
            return None
        return self.tubes[tube_id].get_bbox(frame_id)

    def get_bboxes(self, frame_id, ignored_tube_id=None):
        bboxes = []
        for tube_id, tube in self.tubes.items():
            if tube_id == ignored_tube_id:
                continue
            bbox = tube.get_bbox(frame_id)
            if bbox is not None:
                bboxes.append(bbox)
        return bboxes

    def get_brief_info(self):
        info = []
        for tube in self.tubes.values():
            info.append(tube.to_dict(with_bboxes=False))
        return info
