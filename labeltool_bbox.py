#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QMainWindow
from video_widget import *
from annotation_widget import *


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.init_ui()
        self.show()
        self.action_open.triggered.connect(self.video_widget.open_file)
        self.action_save.triggered.connect(self.video_widget.save_annotations)
        self.action_export.triggered.connect(self.video_widget.export_video)
        self.video_widget.signal_sections_loaded.connect(self.annotation_widget.show_sections)
        self.video_widget.signal_section_changed.connect(self.annotation_widget.select_section)
        self.video_widget.signal_frame_updated.connect(self.update_frame_idx)
        self.video_widget.video.signal_export_progress.connect(self.update_export_progress)
        self.annotation_widget.signal_section_selected.connect(self.video_widget.jump_to_section)
        self.annotation_widget.combobox_word.currentTextChanged.connect(
            self.video_widget.label_frame.update_bbox_label)

    def center_window(self, w, h):
        desktop = QDesktopWidget()
        screen_w = desktop.width()
        screen_h = desktop.height()
        self.setGeometry((screen_w - w) / 2, (screen_h - h) / 2, w, h)

    def init_ui(self):
        self.setWindowTitle('LabelTool')
        self.center_window(800, 600)
        self.init_menubar()
        self.init_statusbar()

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 6)
        grid_layout.setColumnStretch(1, 2)
        self.video_widget = VideoWidget(max_fps=50)
        self.annotation_widget = AnnotationWidget()
        grid_layout.addWidget(self.video_widget, 0, 0)
        grid_layout.addWidget(self.annotation_widget, 0, 1)

        self.central_widget = QWidget(self)
        self.central_widget.setLayout(grid_layout)
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
    def update_frame_idx(self, frame_cursor):
        frame_num = self.video_widget.video.frame_num
        self.label_frame_idx.setText(' Frame {}/{}'.format(
            frame_cursor, frame_num))

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
