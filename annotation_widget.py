import json

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class Annotation(object):

    def __init__(self, filename=None):
        self.data = {}
        self.next_id = 1
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        with open(filename, 'r') as fin:
            self.data = json.load(fin)

    def save(self, filename):
        with open(filename, 'w') as fout:
            json.dump(self.data, fout)

    def add_bbox(frame_idx, rect, label, type, id):
        if str(frame_idx) not in self.data:
            self.data[str(frame_idx)] = []
        self.data[str(frame_idx)].append(
            dict(bbox=rect, label=label, type=type, id=id))

    def del_bbox(frame_idx, id):
        self.data[str(frame_idx)].pop()


class AnnotationWidget(QWidget):
    signal_section_selected = pyqtSignal(int)

    def __init__(self):
        super(AnnotationWidget, self).__init__()
        self.annotation = Annotation()
        self.init_ui()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.lineedit_word.returnPressed.connect(self.add_word)
        # self.installEventFilter(self)

    def init_ui(self):
        self.vbox_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        # self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.hbox_layout = QHBoxLayout()
        self.combobox_word = QComboBox()
        self.lineedit_word = QLineEdit()
        self.hbox_layout.addWidget(self.combobox_word, 1)
        self.hbox_layout.addWidget(self.lineedit_word, 2)
        self.vbox_layout.addWidget(self.list_widget, 8)
        self.vbox_layout.addLayout(self.hbox_layout, 1)
        self.setLayout(self.vbox_layout)

    # def keyPressEvent(self, event):
    #     if event.type() != QEvent.KeyPress:
    #         return
    #     key = event.key()
    #     if key == Qt.Key_Backspace:
    #         items = self.list_widget.selectedItems()
    #         for item in items:
    #             self.del_annotation_item(item)

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
        if self.combobox_word.findText(word) < 0:
            self.combobox_word.addItem(word)
        self.combobox_word.setCurrentText(word)
        self.lineedit_word.setText('')

    @pyqtSlot(str)
    def load_annotation(self, filename):
        self.annotation.load(filename + '.annotation')
        for shot in self.annotation.data['shots']:
            self.list_widget.addItem('{shot[0]} - {shot[1]}'.format(shot=shot))
        self.list_widget.update()

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        section_idx = self.list_widget.row(item)
        # cursor = int(item.text().split(' - ')[0])
        self.signal_section_selected.emit(section_idx)
