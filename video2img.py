import math
import os

import cv2
import numpy as np
from PIL import Image

from video import Annotation


def video2img(filename, out_filename, frame_list=None, frame_interval=1,
              img_per_row=50, max_num=0):
    cap = cv2.VideoCapture(filename)
    if frame_list is None:
        frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_list = range(frame_num)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sample_num = int(len(frame_list) / frame_interval)
    if max_num > 0:
        sample_num = min(sample_num, max_num)
    frames = frame_list[0: len(frame_list): frame_interval][:sample_num]
    rows = int(math.ceil(sample_num / img_per_row))
    cols = img_per_row if rows > 1 else sample_num
    full_img = np.zeros((rows * frame_height, cols * frame_width, 3),
                        dtype=np.uint8)
    for i, frame_idx in enumerate(frames):
        print('frame #', frame_idx)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, img = cap.read()
        row_idx = int(i / img_per_row)
        col_idx = i % img_per_row
        start_x = col_idx * frame_width
        start_y = row_idx * frame_height
        full_img[start_y: start_y + frame_height,
                 start_x: start_x + frame_width, :] = img
    ext = os.path.splitext(out_filename)[-1]
    if ext == '.pdf':
        img_rgb = cv2.cvtColor(full_img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.save(out_filename, 'PDF', resolution=100.0)
    else:
        cv2.imwrite(out_filename, full_img)

if __name__ == '__main__':
    annotation = Annotation('/home/kchen/data/youtube/selected/aOyzrlBnxFs.mp4.annotation')
    annotated_frames = []
    for i, bboxes in annotation.objects().items():
        if len(bboxes) > 0:
            annotated_frames.append(int(i))
    annotated_frames.sort()
    video2img('aOyzr.avi', 'tiger.png', frame_list=annotated_frames,
              frame_interval=10, img_per_row=30, max_num=900)
