#!/usr/bin/env python3

import os
import json
import subprocess


class ShotDetector(object):

    def __init__(self, thr=0.15):
        self.thr = thr
        pass

    def detect(self, filename, fps=None, frame_num=None, save=True):
        if fps is None or frame_num is None:
            import cv2
            cap = cv2.VideoCapture(filename)
            fps = int(round(cap.get(cv2.CAP_PROP_FPS)))
            frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        annotation_file = filename + '.annotation'
        if os.path.isfile(annotation_file):
            with open(annotation_file, 'r') as fin:
                annotation = json.load(fin)
            return annotation['shots']
        scene_ps = subprocess.Popen(
            ('ffprobe', '-show_frames', '-of', 'compact=p=0', '-f', 'lavfi',
             'movie={},select=gt(scene\,{})'.format(filename, self.thr)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        output = scene_ps.stdout.read().decode('utf-8')
        shots = []
        for line in output.split('\n')[15: -1]:
            boundary = int(round(float(line.split('|')[4].split('=')[-1]) * fps))
            if len(shots) == 0:
                shots.append((0, boundary))
            else:
                start = shots[-1][1] + 1
                shots.append((start, boundary))
        shots.append((shots[-1][1] + 1, frame_num - 1))
        if save:
            annotation = dict(shots=shots)
            with open(annotation_file, 'w') as fout:
                json.dump(annotation, fout)
        return shots

if __name__ == '__main__':
    shot_detector = ShotDetector()
    video_dir = '/home/kchen/data/youtube/selected/'
    for entry in os.scandir(video_dir):
        if not entry.is_file():
            continue
        filename = entry.name
        if filename.split('.')[-1] in ['mp4', 'mkv']:
            print(filename)
            shot_detector.detect(video_dir + filename)
