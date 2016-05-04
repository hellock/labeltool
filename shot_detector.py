import os
import json
import subprocess


class ShotDetectot(object):

    def __init__(self, thr=0.15):
        self.thr = thr
        pass

    def detect(self, filename, fps=None, frame_num=None, save=True):
        if fps is None or frame_num is None:
            import cv2
            cap = cv2.VideoCapture(filename)
            fps = int(round(cap.get(cv2.CAP_PROP_FPS)))
            frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        shot_file = filename + '.shot'
        if os.path.isfile(shot_file):
            with open(shot_file, 'r') as fin:
                boundaries = json.load(fin)
            return boundaries
        scene_ps = subprocess.Popen(
            ('ffprobe', '-show_frames', '-of', 'compact=p=0', '-f', 'lavfi',
             'movie={},select=gt(scene\,{})'.format(filename, self.thr)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        output = scene_ps.stdout.read().decode('utf-8')
        boundaries = []
        for line in output.split('\n')[15: -1]:
            boundary = int(round(float(line.split('|')[4].split('=')[-1]) * fps))
            if len(boundaries) == 0:
                boundaries.append((0, boundary))
            else:
                start = boundaries[-1][1]
                boundaries.append((start, boundary))
        boundaries.append((boundaries[-1][1], frame_num))
        if save:
            with open(shot_file, 'w') as fout:
                json.dump(boundaries, fout)
        return boundaries
