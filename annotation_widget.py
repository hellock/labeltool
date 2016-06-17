from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import *


class AnnotationWidget(QWidget):
    signal_tube_selected = pyqtSignal(int)

    def __init__(self):
        super(AnnotationWidget, self).__init__()
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

    def set_words(self, words):
        self.combobox_word.clear()
        for word in words:
            if word.strip() == '':
                continue
            self.combobox_word.addItem(word)

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

    @pyqtSlot(list)
    def show_annotations(self, annotations):
        """show a list of tube info
        format: {id: label: start-end}
        """
        for tube in annotations:
            item_str = '{0[0]}: {0[1]}: {0[2]}-{0[3]}'.format(tube)
            self.list_widget.addItem(item_str)
        self.list_widget.update()
        # add words in annotations to combobox
        unique_labels = set()
        for tube in annotations:
            unique_labels.add(tube[1])
        self.set_words(list(unique_labels))

    # @pyqtSlot(int)
    # def select_section(self, section_idx):
    #     self.list_widget.setCurrentRow(section_idx)

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        tube_info = item.text().split(':')
        tube_id = int(tube_info[0])
        self.combobox_word.setCurrentText(tube_info[1])
        self.signal_tube_selected.emit(tube_id)
