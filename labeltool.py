#!/usr/bin/env python3

import os
import sys
import json
import threading

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from video import Video


class VideoWidget(QWidget):
    signal_play_option = pyqtSignal(int)
    signal_video_loaded = pyqtSignal(str)

    def __init__(self, parent=None, max_buf_size=500):
        super(VideoWidget, self).__init__(parent)
        self.video = Video(max_buf_size=max_buf_size)
        self.max_buf_size = max_buf_size
        self.init_ui()
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.installEventFilter(self)

    def init_ui(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setRowStretch(0, 1)
        self.grid_layout.setRowStretch(1, 10)
        self.grid_layout.setRowStretch(2, 1)
        self.set_slider()
        self.set_label_filename()
        self.set_label_frame()
        self.setLayout(self.grid_layout)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_slider(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setTickInterval(1)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.grid_layout.addWidget(self.slider, 2, 0)

    def set_label_filename(self):
        self.label_filename = QLabel('filename')
        self.label_filename.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self.label_filename, 0, 0)

    def set_label_frame(self):
        self.label_frame = QLabel('video')
        self.label_frame.setAlignment(Qt.AlignCenter)
        self.label_frame.setStyleSheet('border: 1px solid black')
        self.grid_layout.addWidget(self.label_frame, 1, 0)

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            print('key pressed in video filter ', object, key)
            if key == Qt.Key_D:
                self.video.next_frame()
                return True
            elif key == Qt.Key_A:
                self.video.last_frame()
                return True
            elif key == Qt.Key_Left:
                if self.video.play_status >= 0:
                    self.signal_play_option.emit(-1)
                else:
                    self.signal_play_option.emit(0)
                return True
            elif key == Qt.Key_Right:
                if self.video.play_status <= 0:
                    self.signal_play_option.emit(1)
                else:
                    self.signal_play_option.emit(0)
                return True
            elif key == Qt.Key_Space:
                self.video.play_status = 0
                return True
            else:
                print('send to parent ', self.parent())
                print('send to parent\'s parent ', self.parent().parent())
                return False
        else:
            return False

    # def keyPressEvent(self, event):
    #     key = event.key()
    #     print('key pressed in video widget ', key)
    #     if key == Qt.Key_D:
    #         self.video.next_frame()
    #     elif key == Qt.Key_A:
    #         self.video.last_frame()
    #     elif key == Qt.Key_Left:
    #         if self.video.play_status >= 0:
    #             self.signal_play_option.emit(-1)
    #         else:
    #             self.signal_play_option.emit(0)
    #     elif key == Qt.Key_Right:
    #         if self.video.play_status <= 0:
    #             self.signal_play_option.emit(1)
    #         else:
    #             self.signal_play_option.emit(0)
    #     elif key == Qt.Key_Space:
    #         self.video.play_status = 0

    @pyqtSlot()
    def open_file(self):
        self.filename, _ = QFileDialog.getOpenFileName(
            self, 'Load video', './', 'Videos (*.mp4 *.avi *.mkv *.flv *.m4v)')
        if not self.filename:
            return
        disp_name = os.path.basename(self.filename)
        self.label_filename.setText(os.path.basename(disp_name))
        self.video.load(self.filename)
        self.signal_play_option.connect(self.video.play_ctl)
        self.video.signal_frame_updated.connect(self.update_frame)
        self.video.next_frame()
        self.slider.setEnabled(True)
        self.signal_video_loaded.emit(self.filename)

    @pyqtSlot(QPixmap)
    def update_frame(self, pixmap):
        frame_cursor = self.video.frame_cursor
        frame_num = self.video.frame_num
        self.label_frame.setPixmap(
            pixmap.scaled(self.label_frame.width() - 2,
                          self.label_frame.height() - 2,
                          Qt.KeepAspectRatio))
        self.label_frame.update()
        self.slider.setValue(int(frame_cursor * self.slider.maximum() / frame_num))

    @pyqtSlot()
    def on_slider_released(self):
        self.video.play_status = 0
        cursor = int(self.video.frame_num * self.slider.value() / self.slider.maximum())
        self.video.set_pos(cursor)

    @pyqtSlot(int)
    def jump_to_frame(self, cursor):
        self.video.play_status = 0
        self.video.set_pos(cursor)


class AnnotationWidget(QWidget):
    signal_frame_selected = pyqtSignal(int)

    def __init__(self, parrent=None):
        super(AnnotationWidget, self).__init__(parrent)
        self.annotation = {}
        self.init_ui()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.lineedit_word.returnPressed.connect(self.add_word)
        # self.installEventFilter(self)

    def init_ui(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.setVerticalSpacing(14)
        self.grid_layout.setHorizontalSpacing(2)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.combobox = QComboBox()
        self.label_start = QLabel('Start')
        self.label_end = QLabel('End')
        self.lineedit_start = QLineEdit()
        self.lineedit_start.setReadOnly(True)
        self.lineedit_end = QLineEdit()
        self.lineedit_end.setReadOnly(True)
        self.lineedit_word = QLineEdit()
        self.grid_layout.addWidget(self.list_widget, 0, 0, 11, 2)
        self.grid_layout.addWidget(self.label_start, 11, 0, 1, 1)
        self.grid_layout.addWidget(self.label_end, 12, 0, 1, 1)
        self.grid_layout.addWidget(self.lineedit_start, 11, 1, 1, 1)
        self.grid_layout.addWidget(self.lineedit_end, 12, 1, 1, 1)
        self.grid_layout.addWidget(self.combobox, 13, 0, 1, 1)
        self.grid_layout.addWidget(self.lineedit_word, 13, 1, 1, 1)
        self.setLayout(self.grid_layout)

    def keyPressEvent(self, event):
        if event.type() != QEvent.KeyPress:
            return
        key = event.key()
        if key == Qt.Key_Backspace:
            items = self.list_widget.selectedItems()
            for item in items:
                self.del_annotation_item(item)

    def set_start(self, start):
        self.lineedit_start.setText(str(start))

    def set_end(self, end):
        self.lineedit_end.setText(str(end))

    def add_annotation(self, word, start, end):
        if word not in self.annotation:
            self.annotation[word] = []
        self.annotation[word].append([start, end])
        self.list_widget.addItem('{}: {} - {}'.format(word, start, end))

    def save_annotations(self):
        with open(self.filename + '.annotation', 'w') as fout:
            json.dump(self.annotation, fout)

    def asyn_save_annotations(self):
        t = threading.Thread(target=self.save_annotations)
        t.daemon = True
        t.start()

    def del_annotation_item(self, item):
        self.list_widget.takeItem(self.list_widget.row(item))
        self.list_widget.update()
        info = item.text().split(': ')
        word = info[0]
        time_slot = list(map(int, info[1].split(' - ')))
        self.annotation[word].remove(time_slot)

    @pyqtSlot()
    def add_word(self):
        word = self.lineedit_word.text()
        if word.strip() == '':
            return
        if self.combobox.findText(word) < 0:
            self.combobox.addItem(word)
        self.combobox.setCurrentText(word)
        self.lineedit_word.setText('')

    @pyqtSlot(str)
    def load_annotation(self, filename):
        self.list_widget.clear()
        annotation_filename = filename + '.annotation'
        if not os.path.isfile(annotation_filename):
            return
        with open(annotation_filename, 'r') as fin:
            self.annotation = json.load(fin)
        for word in self.annotation:
            for time_slot in self.annotation[word]:
                start = time_slot[0]
                end = time_slot[1]
                self.list_widget.addItem('{}: {} - {}'.format(word, start, end))

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        cursor = int(item.text().split(': ')[1].split(' - ')[0])
        self.signal_frame_selected.emit(cursor)


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        self.init_ui()
        self.show()
        self.action_open.triggered.connect(self.video_widget.open_file)
        self.video_widget.signal_video_loaded.connect(self.annotation_widget.load_annotation)
        self.video_widget.video.signal_frame_updated.connect(self.update_statusbar)
        self.annotation_widget.signal_frame_selected.connect(self.video_widget.jump_to_frame)
        self.annotation_widget.installEventFilter(self)

    def set_menubar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menu_file = menubar.addMenu('&File')
        self.action_open = QAction('&Open', menubar)
        self.action_open.setShortcut('Ctrl+O')
        menu_file.addAction(self.action_open)

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

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def center_window(self, w, h):
        desktop = QDesktopWidget()
        screen_w = desktop.width()
        screen_h = desktop.height()
        self.setGeometry((screen_w - w) / 2, (screen_h - h) / 2, w, h)

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            print('event filter in mainwin ', event.key())
            key = event.key()
            if key == Qt.Key_S:
                print('S', ...)
                self.annotation_widget.set_start(self.video_widget.video.frame_cursor)
                return True
            elif key == Qt.Key_T:
                self.annotation_widget.set_end(self.video_widget.video.frame_cursor)
                return True
            elif key == Qt.Key_Enter or key == Qt.Key_Return:
                if self.annotation_widget.lineedit_word.hasFocus():
                    return False
                else:
                    self.add_annotation()
                    return True
            else:
                return False
        return False

    # def keyPressEvent(self, event):
    #     print('event in main window', ...)
    #     key = event.key()
    #     if key == Qt.Key_S:
    #         self.annotation_widget.set_start(self.video_widget.video.frame_cursor)
    #     elif key == Qt.Key_T:
    #         self.annotation_widget.set_end(self.video_widget.video.frame_cursor)
    #     elif key == Qt.Key_Enter or key == Qt.Key_Return:
    #         if not self.annotation_widget.lineedit_word.hasFocus():
    #             self.add_annotation()
    #     elif key == Qt.Key_Backspace:
    #         if self.listwidget.hasFocus():
    #             item = self.listwidget.currentItem()
    #             self.listwidget.takeItem(self.listwidget.row(item))
    #             self.listwidget.update()
    #             info = item.text().split(': ')
    #             word = info[0]
    #             time_slot = list(map(int, info[1].split(' - ')))
    #             print(time_slot)
    #             self.annotation[word].remove(time_slot)

    def add_annotation(self):
        word = self.annotation_widget.combobox.currentText()
        if word.strip() == '':
            return
        start = int(self.annotation_widget.lineedit_start.text())
        end = int(self.annotation_widget.lineedit_end.text())
        self.annotation_widget.add_annotation(word, start, end)

    @pyqtSlot(QPixmap)
    def update_statusbar(self, pixmap):
        frame_cursor = self.video_widget.video.frame_cursor
        frame_num = self.video_widget.video.frame_num
        self.statusBar().showMessage(' Frame {}/{}'.format(
            frame_cursor, frame_num))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform == 'linux':
        app.setStyle('Fusion')
    window = MainWindow()
    sys.exit(app.exec_())
