import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from image_label import ImageLabel
from video import *


class VideoWidget(QWidget):
    signal_play_ctrl = pyqtSignal(VideoStatus)
    signal_annotation_loaded = pyqtSignal(list)
    signal_section_changed = pyqtSignal(int)

    def __init__(self, parent=None, with_filename=True, with_slider=True,
                 max_buf_size=500, max_fps=0):
        super(VideoWidget, self).__init__(parent)
        self.with_filename = with_filename
        self.with_slider = with_slider
        self.video = Video(max_buf_size=max_buf_size, max_fps=max_fps)
        self.init_ui()
        self.installEventFilter(self)
        if self.with_slider:
            self.slider.sliderReleased.connect(self.on_slider_released)
        self.video.signal_frame_updated.connect(self.update_frame)
        self.label_frame.signal_bbox_added.connect(self.video.set_tracker)
        self.label_frame.signal_bbox_deleted.connect(self.video.del_tracker)

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
                self.video.play_ctrl(VideoStatus.frame_forward)
                return True
            elif key == Qt.Key_A:
                self.video.play_ctrl(VideoStatus.frame_backward)
                return True
            elif key == Qt.Key_S:
                self.video.annotation.save()
                if self.label_frame.bbox_label is not None:
                    self.video.add_tube(self.label_frame.bbox_label)
                    self.label_frame.toggle_reticle(True)
                return True
            elif key == Qt.Key_Left:
                if self.video.status == VideoStatus.play_backward:
                    self.video.play_ctrl(VideoStatus.pause)
                elif self.video.status != VideoStatus.not_loaded:
                    self.video.play_ctrl(VideoStatus.play_backward)
                return True
            elif key == Qt.Key_Right:
                if self.video.status == VideoStatus.play_forward:
                    self.video.play_ctrl(VideoStatus.pause)
                elif self.video.status != VideoStatus.not_loaded:
                    self.video.play_ctrl(VideoStatus.play_forward)
                return True
            elif key == Qt.Key_Space:
                self.video.play_ctrl(VideoStatus.pause)
                return True
        return False

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
        self.jump_to_frame(1)
        self.signal_annotation_loaded.emit(
            self.video.annotation.get_brief_info())

    @pyqtSlot(VideoFrame, dict)
    def update_frame(self, frame, bboxes):
        self.label_frame.show_img(frame)
        self.label_frame.update_bboxes(bboxes)
        frame_id = frame.id
        frame_num = self.video.frame_num
        if self.with_slider:
            self.slider.setValue(
                int(self.slider.maximum() * frame_id / frame_num))

    @pyqtSlot()
    def on_slider_released(self):
        progress = self.slider.value() / self.slider.maximum()
        cursor = int(self.video.frame_num * progress)
        self.jump_to_frame(cursor)

    @pyqtSlot(int)
    def jump_to_frame(self, cursor):
        self.label_frame.clear_bboxes()
        self.video.jump_to_frame(cursor)

    @pyqtSlot(int)
    def jump_to_tube(self, tube_id):
        self.video.jump_to_tube(tube_id)

    @pyqtSlot()
    def save_annotations(self):
        self.video.annotation.save()

    @pyqtSlot()
    def export_video(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 'Export video', './', 'Videos (*.avi)')
        t = threading.Thread(target=self.video.export,
                             kwargs=dict(filename=filename))
        t.daemon = True
        t.start()
