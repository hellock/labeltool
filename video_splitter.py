#!/usr/bin/env python3

import os
import json
import subprocess

import ckutils


class VideoSplitter(object):

    def __init__(self, thr=0.15):
        self.thr = thr
        pass

    def split(self, filename, fps=None, frame_num=None, save=True):
        if fps is None or frame_num is None:
            import cv2
            cap = cv2.VideoCapture(filename)
            fps = int(round(cap.get(cv2.CAP_PROP_FPS)))
            frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        config_file = filename + '.cfg'
        if os.path.isfile(config_file):
            with open(config_file, 'r') as fin:
                config = json.load(fin)
            return config['sections']
        scene_ps = subprocess.Popen(
            ('ffprobe', '-show_frames', '-of', 'compact=p=0', '-f', 'lavfi',
             'movie={},select=gt(scene\,{})'.format(filename, self.thr)),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        output = scene_ps.stdout.read().decode('utf-8')
        boundaries = []
        for line in output.split('\n')[15: -1]:
            time_point = float(line.split('|')[4].split('=')[-1])
            boundaries.append(int(round(time_point * fps)))
        sections = [[0, boundaries[0]]]
        for bd in boundaries[1:]:
            start = sections[-1][1] + 1
            if bd - start == 1:
                sections[-1][1] = bd
            else:
                sections.append([start, bd - 1])
        sections.append((sections[-1][1] + 1, frame_num))
        if save:
            config = dict(sections=sections)
            with open(config_file, 'w') as fout:
                json.dump(config, fout)
        return sections

if __name__ == '__main__':
    vs = VideoSplitter()
    video_dir = '/home/kchen/data/youtube/selected/'
    for filename in ckutils.scandir(video_dir, ['mp4', 'mkv']):
        print(filename)
        sections = vs.split(video_dir + filename)
        print(len(sections), 'sections')
