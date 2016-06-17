import os


def scandir(path='.', ext_filter=None):
    if isinstance(ext_filter, str):
        ext_filter = [ext_filter]
    for entry in os.scandir(path):
        if not entry.is_file():
            continue
        filename = entry.name
        if ext_filter is None:
            yield filename
        elif os.path.splitext(filename)[1][1:] in ext_filter:
            yield filename


def int2str(i, zero_num=0):
    if zero_num == 0:
        return str(i)
    else:
        return '{0:0{1}d}'.format(i, zero_num)


class VideoUtil(object):

    @staticmethod
    def video2frames(video_file, frame_dir):
        pass

    @staticmethod
    def frames2video(frame_dir, video_file, start=0, end=0):
        pass
