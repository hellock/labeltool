#!/usr/bin/env python3

import os
import sys
import json
import threading

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from video import Video


class MainWindow(QMainWindow):
    signal_play_option = pyqtSignal(int)

    def __init__(self):
        QMainWindow.__init__(self)

        self.init_ui()
        self.show()
        self.annotation = {}

        self.slider.sliderReleased.connect(self.on_slider_released)

    def init_ui(self):
        self.setWindowTitle('LabelTool')
        self.center_window(800, 600)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menu_file = menubar.addMenu('&File')
        action_open = QAction('&Open', menubar)
        action_open.setShortcut('Ctrl+O')
        action_open.triggered.connect(self.open_file)
        menu_file.addAction(action_open)

        self.statusBar()

        self.label_filename = QLabel('filename', self.centralWidget())
        self.label_filename.setAlignment(Qt.AlignCenter)

        self.label_frame = QLabel('video', self.centralWidget())
        self.label_frame.setAlignment(Qt.AlignCenter)
        self.label_frame.setStyleSheet('border: 1px solid black')

        self.slider = QSlider(Qt.Horizontal, self.centralWidget())
        self.slider.setRange(0, 1000)
        self.slider.setTickInterval(1)
        self.slider.setValue(0)
        self.slider.setEnabled(False)

        grid_layout = QGridLayout()
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 8)
        grid_layout.setRowStretch(2, 2)
        grid_layout.setColumnStretch(0, 6)
        grid_layout.setColumnStretch(1, 2)
        grid_layout.addWidget(self.label_filename, 0, 0, 1, 1)
        grid_layout.addWidget(self.label_frame, 1, 0, 1, 1)
        grid_layout.addWidget(self.slider, 2, 0, 1, 2)

        self.label_start = QLabel('Start')
        self.label_end = QLabel('End')
        self.combobox = QComboBox(self.centralWidget())
        self.lineedit_start = QLineEdit(self.centralWidget())
        self.lineedit_start.setReadOnly(True)
        self.lineedit_end = QLineEdit(self.centralWidget())
        self.lineedit_end.setReadOnly(True)
        self.lineedit_word = QLineEdit(self.centralWidget())
        self.lineedit_word.returnPressed.connect(self.add_word)

        layout_annotation = QGridLayout()
        layout_annotation.setVerticalSpacing(14)
        layout_annotation.setHorizontalSpacing(2)
        self.listwidget = QListWidget(self.centralWidget())
        layout_annotation.addWidget(self.listwidget, 0, 0, 11, 2)
        layout_annotation.addWidget(self.label_start, 11, 0, 1, 1)
        layout_annotation.addWidget(self.label_end, 12, 0, 1, 1)
        layout_annotation.addWidget(self.lineedit_start, 11, 1, 1, 1)
        layout_annotation.addWidget(self.lineedit_end, 12, 1, 1, 1)
        layout_annotation.addWidget(self.combobox, 13, 0, 1, 1)
        layout_annotation.addWidget(self.lineedit_word, 13, 1, 1, 1)

        grid_layout.addLayout(layout_annotation, 0, 1, 2, 1)

        self.central_widget = QWidget(self)
        self.central_widget.setLayout(grid_layout)
        self.setCentralWidget(self.central_widget)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def center_window(self, w, h):
        desktop = QDesktopWidget()
        screen_w = desktop.width()
        screen_h = desktop.height()
        self.setGeometry((screen_w - w) / 2, (screen_h - h) / 2, w, h)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_D:
            self.video.next_frame()
        elif key == Qt.Key_A:
            self.video.last_frame()
        elif key == Qt.Key_Left:
            if self.video.play_status >= 0:
                self.signal_play_option.emit(-1)
            else:
                self.signal_play_option.emit(0)
        elif key == Qt.Key_Right:
            if self.video.play_status <= 0:
                self.signal_play_option.emit(1)
            else:
                self.signal_play_option.emit(0)
        elif key == Qt.Key_Space:
            self.video.play_status = 0
        elif key == Qt.Key_S:
            self.set_start(self.video.frame_cursor)
        elif key == Qt.Key_T:
            self.set_end(self.video.frame_cursor)
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            if not self.lineedit_word.hasFocus():
                self.add_annotation()
                if self.listwidget.count() % 5 == 0:
                    self.save_annotations_periodicly()
        elif key == Qt.Key_Backspace:
            if self.listwidget.hasFocus():
                item = self.listwidget.currentItem()
                self.listwidget.takeItem(self.listwidget.row(item))
                self.listwidget.update()
                info = item.text().split(': ')
                word = info[0]
                time_slot = list(map(int, info[1].split(' - ')))
                print(time_slot)
                self.annotation[word].remove(time_slot)

    def set_start(self, start):
        self.lineedit_start.setText(str(start))

    def set_end(self, end):
        self.lineedit_end.setText(str(end))

    def load_annotation(self, filename):
        with open(filename, 'r') as fin:
            annotation = json.load(fin)
        self.annotation = annotation
        for word in annotation:
            for time_slot in annotation[word]:
                start = time_slot[0]
                end = time_slot[1]
                self.listwidget.addItem('{}: {} - {}'.format(word, start, end))

    def add_annotation(self):
        start = int(self.lineedit_start.text())
        end = int(self.lineedit_end.text())
        word = self.combobox.currentText()
        if word not in self.annotation:
            self.annotation[word] = []
        self.annotation[word].append([start, end])
        self.listwidget.addItem('{}: {} - {}'.format(word, start, end))

    def save_annotations_periodicly(self):
        t = threading.Thread(target=self.save_annotations)
        t.daemon = True
        t.start()

    def save_annotations(self):
        with open(self.filename + '.annotation', 'w') as fout:
            json.dump(self.annotation, fout)

    @pyqtSlot()
    def open_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(
            self, 'Load video', './', 'Videos (*.mp4 *.avi *.mkv *.flv *.m4v)')
        if not self.filename:
            return
        disp_name = os.path.basename(self.filename)
        self.label_filename.setText(os.path.basename(disp_name))
        self.video = Video(self.filename)
        self.signal_play_option.connect(self.video.play_ctl)
        self.video.signal_frame_updated.connect(self.on_frame_updated)
        self.video.next_frame()
        self.slider.setEnabled(True)
        self.listwidget.clear()
        if os.path.isfile(self.filename + '.annotation'):
            self.load_annotation(self.filename + '.annotation')

    @pyqtSlot()
    def add_word(self):
        word = self.lineedit_word.text()
        if self.combobox.findText(word) < 0:
            self.combobox.addItem(word)
        self.combobox.setCurrentText(word)
        self.lineedit_word.setText('')

    @pyqtSlot(bool, QPixmap)
    def on_frame_updated(self, success, pixmap):
        if success:
            frame_cursor = self.video.frame_cursor
            frame_num = self.video.frame_num
            self.label_frame.setPixmap(
                pixmap.scaled(self.label_frame.width() - 2,
                              self.label_frame.height() - 2,
                              Qt.KeepAspectRatio))
            self.label_frame.update()
            self.statusBar().showMessage(' Frame {}/{}'.format(
                frame_cursor, frame_num))
            self.slider.setValue(int(frame_cursor * self.slider.maximum() / frame_num))

    @pyqtSlot()
    def on_slider_released(self):
        self.video.play_status = 0
        cursor = int(self.video.frame_num * self.slider.value() / self.slider.maximum())
        self.video.set_pos(cursor)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'linux':
        app.setStyle('Fusion')
    window = MainWindow()
    sys.exit(app.exec_())
