import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from annotation import Annotation
from bbox import BoundingBox
from ckutils.cv import *
from image_label import ImageLabel
from tracker import Tracker
from video import *


class VideoWidget(QWidget):

    frame_updated = pyqtSignal(int)
    tube_annotated = pyqtSignal(dict)
    annotation_loaded = pyqtSignal(list)
    export_progress_updated = pyqtSignal(int)

    def __init__(self, parent=None, with_filename=True, with_slider=True,
                 max_buf_size=500, max_fps=0):
        super(VideoWidget, self).__init__(parent)
        self.with_filename = with_filename
        self.with_slider = with_slider
        self.video = Video(max_buf_size=max_buf_size, max_fps=max_fps)
        self.annotation = Annotation()
        self.tube_id = 0
        self.tracker = None
        self.sim_thr = 0.9
        self.init_ui()
        self.installEventFilter(self)
        if self.with_slider:
            self.slider.sliderReleased.connect(self.on_slider_released)
        self.label_frame.bbox_added.connect(self.set_tracker)
        self.label_frame.bbox_deleted.connect(self.del_tracker)
        self.video.frame_updated.connect(self.update_frame)
        self.video.export_progress_updated.connect(self.update_export_progress)

    def init_ui(self):
        self.vbox_layout = QVBoxLayout()
        if self.with_filename:
            self.init_label_filename()
        self.init_label_frame()
        if self.with_slider:
            self.init_slider()
        self.setLayout(self.vbox_layout)
        self.setFocusPolicy(Qt.StrongFocus)

    def init_label_filename(self):
        self.label_filename = QLabel('filename')
        self.label_filename.setAlignment(Qt.AlignCenter)
        self.vbox_layout.addWidget(self.label_filename, 1)

    def init_label_frame(self):
        self.label_frame = ImageLabel('video')
        self.label_frame.setAlignment(Qt.AlignCenter)
        self.label_frame.setStyleSheet('border: 1px solid black')
        self.vbox_layout.addWidget(self.label_frame, 10)

    def init_slider(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setTickInterval(1)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.vbox_layout.addWidget(self.slider, 1)

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_D:
                self.frame_forward()
                return True
            elif key == Qt.Key_A:
                self.frame_backward()
                return True
            elif key == Qt.Key_S:
                self.last_keyframe = self.cursor()
                self.new_tube()
                return True
            elif key == Qt.Key_Left:
                if self.status() == VideoStatus.play_backward:
                    self.pause()
                elif self.video.status != VideoStatus.not_loaded:
                    self.play_backward()
                return True
            elif key == Qt.Key_Right:
                if self.status() == VideoStatus.play_forward:
                    self.pause()
                elif self.status() != VideoStatus.not_loaded:
                    self.play_forward()
                return True
            elif key == Qt.Key_Space:
                self.pause()
                return True
        return False

    def frame_forward(self):
        if self.tracker is not None:
            ori_hist = color_hist(self.tracker.init_region, 16)
            if self.cursor() >= self.annotation.tube_end(self.tube_id):
                self.last_keyframe = self.cursor()
        cnt = 0
        while cnt < 10:
            frame = self.video.frame_forward()
            self.update_frame(frame)
            if (self.tracker is None or
                    self.cursor() < self.annotation.tube_end(self.tube_id)):
                break
            bbox = self.tracker.bbox
            hist = color_hist(
                frame.raw_img[bbox.left: bbox.right, bbox.top: bbox.bottom], 16)
            if compare_hist(hist, ori_hist) < self.sim_thr:
                break
            cnt += 1

    def frame_backward(self):
        frame = self.video.frame_backward()
        self.update_frame(frame)

    def play_forward(self):
        self.video.play_forward()

    def play_backward(self):
        self.video.play_backward()

    def pause(self):
        self.video.pause()

    def jump_to_frame(self, frame_id):
        self.clear_tracker()
        frame = self.video.jump_to_frame(frame_id)
        self.update_frame(frame)

    def status(self):
        return self.video.status

    def cursor(self):
        return self.video.cursor

    def frame_cnt(self):
        return self.video.frame_cnt

    def current_frame(self):
        return self.video.current_frame()

    def new_tube(self):
        label = self.label_frame.bbox_label
        if label is not None:
            self.tube_id = self.annotation.next_tube_id
            self.annotation.add_tube(label, self.cursor())
            self.label_frame.toggle_reticle(True)

    def clear_tracker(self):
        self.tracker = None

    def reset_tube_id(self):
        self.tube_id = 0

    def track(self, frame):
        frame_rect = BoundingBox(None, 0, 0, 0,
                                 self.video.width, self.video.height)
        bbox, score = self.tracker.update(frame)
        bbox = bbox.intersected(frame_rect)
        return bbox

    def adjust_track_bboxes(self, bbox):
        self.annotation.interpolate(self.tube_id, bbox, self.last_keyframe,
                                    self.cursor())

    @pyqtSlot(VideoFrame)
    def update_frame(self, frame):
        # get bounding boxes of current tube and other tubes
        bboxes = dict()
        if (self.tracker is not None and self.video.is_forward() and
                self.cursor() > self.annotation.tube_end(self.tube_id)):
            bboxes['current_tube'] = self.track(frame)
            self.annotation.set_bbox(self.tube_id, self.cursor(),
                                     bboxes['current_tube'])
        else:
            bboxes['current_tube'] = self.annotation.get_bbox(
                self.tube_id, self.cursor())
        bboxes['other_tubes'] = self.annotation.get_bboxes(
            self.cursor(), self.tube_id)
        # show the frame and corresponding bounding boxes
        self.label_frame.display(frame)
        self.label_frame.update_bboxes(bboxes)
        # update slider position
        if self.with_slider:
            self.slider.setValue(
                int(self.slider.maximum() * frame.id / self.frame_cnt()))
        # emit the frame id to the main window to update status bar
        self.frame_updated.emit(frame.id)

    @pyqtSlot(BoundingBox)
    def set_tracker(self, bbox):
        if self.tracker is not None and self.cursor() > self.last_keyframe + 1:
            self.adjust_track_bboxes(bbox)
        self.tracker = Tracker()
        self.tracker.start_track(self.current_frame(), bbox)
        self.annotation.set_bbox(self.tube_id, self.cursor(), bbox)

    @pyqtSlot()
    def del_tracker(self):
        self.clear_tracker()
        self.annotation.del_later_bboxes(self.tube_id, self.cursor())
        self.annotation.save()
        tube_info = self.annotation.tube(self.tube_id).to_dict(with_bboxes=False)
        self.tube_annotated.emit(tube_info)
        self.reset_tube_id()

    @pyqtSlot()
    def on_slider_released(self):
        progress = self.slider.value() / self.slider.maximum()
        frame_id = max(int(round(self.frame_cnt() * progress)), 1)
        self.jump_to_frame(frame_id)

    @pyqtSlot(int)
    def jump_to_tube(self, tube_id):
        self.tube_id = tube_id
        self.jump_to_frame(self.annotation.tube_start(tube_id))

    @pyqtSlot(str)
    def update_bbox_label(self, label):
        self.label_frame.update_bbox_label(label)

    @pyqtSlot()
    def open_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(
            self, 'Load video', '/home/kchen/data/youtube/selected/',
            'Videos (*.mp4 *.avi *.mkv *.flv *.m4v)')
        if not self.filename:
            return
        if self.with_filename:
            self.label_filename.setText(os.path.basename(self.filename))
        if self.with_slider:
            self.slider.setEnabled(True)
        self.video.load(self.filename)
        self.annotation.load(self.filename + '.annotation')
        self.annotation_loaded.emit(self.annotation.get_brief_info())
        self.jump_to_frame(1)

    @pyqtSlot()
    def export_video(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export video', './', 'Videos (*.avi)')
        t = threading.Thread(target=self.video.export,
                             kwargs=dict(out_file=filename,
                                         annotation=self.annotation))
        t.daemon = True
        t.start()

    @pyqtSlot(int)
    def update_export_progress(self, progress):
        self.export_progress_updated.emit(progress)

    @pyqtSlot()
    def save_annotation(self):
        self.annotation.save()
