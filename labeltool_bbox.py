#!/usr/bin/env python3

import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from annotation_widget import AnnotationWidget
from video_widget import VideoWidget


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.init_ui()
        # menu actions
        self.action_open.triggered.connect(self.video_widget.open_file)
        self.action_save.triggered.connect(self.video_widget.save_annotation)
        self.action_export.triggered.connect(self.video_widget.export_video)
        # video widget signals
        self.video_widget.annotation_loaded.connect(
            self.annotation_widget.show_tubes)
        self.video_widget.frame_updated.connect(self.update_frame_id)
        self.video_widget.tube_annotated.connect(
            self.annotation_widget.add_tube)
        self.video_widget.export_progress_updated.connect(
            self.update_export_progress)
        # annotation widget signals
        self.annotation_widget.combobox_word.currentTextChanged.connect(
            self.video_widget.update_bbox_label)
        self.annotation_widget.tube_selected.connect(
            self.video_widget.jump_to_tube)
        self.annotation_widget.tube_deleted.connect(
            self.video_widget.del_tube)
        # show the window
        self.show()

    def center_window(self, w, h):
        desktop = QDesktopWidget()
        screen_w = desktop.width()
        screen_h = desktop.height()
        self.setGeometry((screen_w - w) / 2, (screen_h - h) / 2, w, h)

    def init_ui(self):
        self.setWindowTitle('LabelTool')
        self.center_window(1200, 800)
        self.init_menubar()
        self.init_statusbar()

        self.video_widget = VideoWidget(max_fps=50)
        self.annotation_widget = AnnotationWidget()

        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.video_widget, 3)
        self.hbox_layout.addWidget(self.annotation_widget, 1)

        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)

    def init_menubar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menu_file = menubar.addMenu('&File')
        self.action_open = QAction('&Open', menubar)
        self.action_open.setShortcut('Ctrl+O')
        menu_file.addAction(self.action_open)
        self.action_save = QAction('&Save', menubar)
        self.action_save.setShortcut('Ctrl+S')
        menu_file.addAction(self.action_save)
        self.action_export = QAction('&Export', menubar)
        self.action_export.setShortcut('Ctrl+E')
        menu_file.addAction(self.action_export)

    def init_statusbar(self):
        statusbar = self.statusBar()
        self.label_frame_idx = QLabel()
        self.progressbar_export = QProgressBar()
        self.progressbar_export.setRange(0, 100)
        self.progressbar_export.setVisible(False)
        statusbar.addWidget(self.label_frame_idx)
        statusbar.addPermanentWidget(self.progressbar_export)

    @pyqtSlot(int)
    def update_frame_id(self, frame_id):
        total_num = self.video_widget.frame_cnt()
        self.label_frame_idx.setText(' Frame {}/{}'.format(frame_id, total_num))

    @pyqtSlot(int)
    def update_export_progress(self, progress):
        if not self.progressbar_export.isVisible():
            self.progressbar_export.setVisible(True)
        self.progressbar_export.setValue(progress)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'linux':
        app.setStyle('Fusion')
    window = MainWindow()
    sys.exit(app.exec_())
