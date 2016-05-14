import os
import json
from collections import OrderedDict

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from bbox import BoundingBox


class Annotation(object):

    def __init__(self, filename=None):
        self.data = OrderedDict(shots=[], objects=OrderedDict())
        self.next_id = 1
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        with open(filename, 'r') as fin:
            self.data = json.load(fin)
        if 'objects' not in self.data:
            self.data['objects'] = OrderedDict()

    def save(self, filename):
        with open(filename, 'w') as fout:
            json.dump(self.data, fout)

    def shots(self):
        return self.data['shots']

    def objects(self):
        return self.data['objects']

    def clear_bbox(self, frame_idx):
        self.data['objects'][str(frame_idx)] = []

    def add_bbox(self, frame_idx, bbox):
        if str(frame_idx) not in self.data['objects']:
            self.data['objects'][str(frame_idx)] = []
        self.data['objects'][str(frame_idx)].append(
            dict(bbox=bbox.to_list(), label=bbox.label, mode=bbox.mode))

    def del_bbox(self, frame_idx, bbox_idx):
        self.data['objects'][str(frame_idx)].pop(bbox_idx)


class AnnotationWidget(QWidget):
    signal_shots_loaded = pyqtSignal(list)
    signal_section_selected = pyqtSignal(int)
    signal_bboxes = pyqtSignal(list)

    def __init__(self):
        super(AnnotationWidget, self).__init__()
        self.annotation = Annotation()
        self.init_ui()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.lineedit_word.returnPressed.connect(self.add_word)

    def init_ui(self):
        self.vbox_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.hbox_layout = QHBoxLayout()
        self.combobox_word = QComboBox()
        self.lineedit_word = QLineEdit()
        self.hbox_layout.addWidget(self.combobox_word, 1)
        self.hbox_layout.addWidget(self.lineedit_word, 2)
        self.vbox_layout.addWidget(self.list_widget, 8)
        self.vbox_layout.addLayout(self.hbox_layout, 1)
        self.setLayout(self.vbox_layout)

    @pyqtSlot()
    def add_word(self):
        word = self.lineedit_word.text()
        if word.strip() == '':
            return
        if self.combobox_word.findText(word) < 0:
            self.combobox_word.addItem(word)
        self.combobox_word.setCurrentText(word)
        self.combobox_word.currentTextChanged.emit(word)
        self.lineedit_word.setText('')

    @pyqtSlot(str)
    def load_annotation(self, filename):
        self.filename = filename + '.annotation'
        if os.path.isfile(self.filename):
            self.annotation.load(self.filename)
            self.signal_shots_loaded.emit(self.annotation.shots())
        for shot in self.annotation.data['shots']:
            self.list_widget.addItem('{shot[0]} - {shot[1]}'.format(shot=shot))
        self.list_widget.update()

    @pyqtSlot(int, list)
    def add_annotation(self, frame_idx, bboxes):
        print(frame_idx, bboxes)
        self.annotation.clear_bbox(frame_idx)
        for bbox in bboxes:
            self.annotation.add_bbox(frame_idx, bbox)
        print(self.annotation.objects())

    @pyqtSlot(int, BoundingBox)
    def add_bbox(self, frame_idx, bbox):
        self.annotation.add_bbox(frame_idx, bbox)

    @pyqtSlot(int, int)
    def del_bbox(self, frame_idx, bbox_idx):
        self.annotation.del_bbox(frame_idx, bbox_idx)

    @pyqtSlot()
    def save_annotations(self):
        with open(self.filename, 'w') as fout:
            json.dump(self.annotation.data, fout)

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        section_idx = self.list_widget.row(item)
        self.signal_section_selected.emit(section_idx)
