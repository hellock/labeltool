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
        self.video_widget.signal_frame_updated.connect(self.update_statusbar)
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
        self.set_menubar()
        self.statusBar()

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 6)
        grid_layout.setColumnStretch(1, 2)
        self.video_widget = VideoWidget()
        self.annotation_widget = AnnotationWidget()
        grid_layout.addWidget(self.video_widget, 0, 0)
        grid_layout.addWidget(self.annotation_widget, 0, 1)

        self.central_widget = QWidget(self)
        self.central_widget.setLayout(grid_layout)
        self.setCentralWidget(self.central_widget)

    def set_menubar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menu_file = menubar.addMenu('&File')
        self.action_open = QAction('&Open', menubar)
        self.action_open.setShortcut('Ctrl+O')
        menu_file.addAction(self.action_open)

    @pyqtSlot(int)
    def update_statusbar(self, frame_cursor):
        frame_num = self.video_widget.video.frame_num
        self.statusBar().showMessage(' Frame {}/{}'.format(
            frame_cursor, frame_num))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'linux':
        app.setStyle('Fusion')
    window = MainWindow()
    sys.exit(app.exec_())
