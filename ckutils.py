"""Some useful functions and classes written by Kai Chen
"""

import os

import cv2


def scandir(path='.', ext=None):
    if isinstance(ext, str):
        ext = [ext]
    for entry in os.scandir(path):
        if not entry.is_file():
            continue
        filename = entry.name
        if ext is None:
            yield filename
        elif os.path.splitext(filename)[1][1:] in ext:
            yield filename


def int2str(i, zero_num=0):
    if zero_num == 0:
        return str(i)
    else:
        return '{0:0{1}d}'.format(i, zero_num)


def str_list(num_list):
    return list(map(str, num_list))


def int_list(str_list):
    return list(map(int, str_list))


class VideoUtil(object):

    @classmethod
    def load_video(cls, filename):
        """load a video file
        Return a VideoCapture object and a dict containing basic infomation
        of the video.
        """
        if not os.path.isfile(filename):
            print('video file not found.')
            return
        vreader = cv2.VideoCapture(filename)
        info = dict()
        info['width'] = int(vreader.get(cv2.CAP_PROP_FRAME_WIDTH))
        info['height'] = int(vreader.get(cv2.CAP_PROP_FRAME_HEIGHT))
        info['fps'] = int(round(vreader.get(cv2.CAP_PROP_FPS)))
        info['frame_cnt'] = int(vreader.get(cv2.CAP_PROP_FRAME_COUNT))
        return (vreader, info)

    @classmethod
    def check_pos(cls, vreader, pos):
        cur_pos = vreader.get(cv2.CAP_PROP_POS_FRAMES)
        assert(cur_pos <= pos)
        if cur_pos < pos:
            for i in range(pos - cur_pos):
                vreader.read()

    @classmethod
    def video2frames(cls, video_file, frame_dir, index_start=0,
                     filename_digit=5, ext='jpg', start=0, max_num=0,
                     print_interval=0):
        """read a video and write the frames into a directory
        If `filename_digit` is set to 0, then the filename will not be padded
        with zeros.
        """
        if not os.path.isfile(video_file):
            print('video file not found.')
            return
        if not os.path.isdir(frame_dir):
            os.makedirs(frame_dir)
        vreader = cv2.VideoCapture(video_file)
        frame_cnt = int(vreader.get(cv2.CAP_PROP_FRAME_COUNT))
        if max_num == 0:
            task_num = frame_cnt - start
        else:
            task_num = min(frame_cnt - start, max_num)
        if task_num <= 0:
            print('total frame number is less than start index.')
            return
        if start > 0:
            vreader.set(cv2.CAP_PROP_POS_FRAMES, start)
            cls.check_pos(vreader, start)
        converted = 0
        while vreader.isOpened() and converted < task_num:
            ret, img = vreader.read()
            if not ret:
                break
            filename = os.path.join(
                frame_dir,
                int2str(converted + index_start, filename_digit) + '.' + ext)
            cv2.imwrite(filename, img)
            converted += 1
            if print_interval > 0 and converted % print_interval == 0:
                print('video2frame progress: {}/{}'.format(converted, task_num))
        vreader.release()

    @classmethod
    def frames2video(cls, frame_dir, video_file, fps=30, fourcc='XVID',
                     filename_digit=5, ext='jpg', start=0, end=0):
        """read the frame images from a directory and write to a video
        """
        if end == 0:
            max_idx = len([name for name in scandir(frame_dir, ext)]) - 1
        else:
            max_idx = end
        first_file = os.path.join(
            frame_dir, int2str(start, filename_digit) + '.' + ext)
        if not os.path.isfile(first_file):
            print('first frame not found.')
            return
        img = cv2.imread(first_file)
        height, width = img.shape[:2]
        vwriter = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*fourcc),
                                  fps, (width, height))
        idx = start
        while vwriter.isOpened() and idx <= max_idx:
            filename = os.path.join(
                frame_dir, int2str(idx, filename_digit) + '.' + ext)
            img = cv2.imread(filename)
            vwriter.write(img)
            idx += 1
        vwriter.release()


class Rect(object):

    @classmethod
    def from_points(pt1, pt2):
        x = min(pt1[0], pt2[0])
        y = min(pt1[1], pt2[1])
        w = abs(pt1[0] - pt2[0]) + 1
        h = abs(pt1[1] - pt2[1]) + 1
        return Rect(x, y, w, h)

    @classmethod
    def from_qrect(cls, qrect):
        return cls(qrect.x(), qrect.y(), qrect.width(), qrect.height())

    def __init__(self, x, y, w, h, type='xywh'):
        self._x = x
        self._y = y
        if type == 'xywh':
            self._w = w
            self._h = h
        elif type == 'ltrb':
            self._w = w - x + 1
            self._h = h - y + 1

    def __iter__(self):
        for val in (self._x, self._y, self._w, self.h):
            yield val

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def w(self):
        return self._w

    @property
    def h(self):
        return self._h

    @property
    def right(self):
        return self._x + self._w - 1

    @property
    def bottom(self):
        return self._y + self._h - 1

    def copy(self):
        return Rect(*list(self))

    def scale(self, ratio):
        self._x *= ratio
        self._y *= ratio
        self._w *= ratio
        self._h *= ratio

    def shift(self, dx, dy):
        self._x += dx
        self._y += dy
