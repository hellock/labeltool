from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import *


class AnnotationWidget(QWidget):
    signal_section_selected = pyqtSignal(int)

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
    def show_sections(self, sections):
        for section in sections:
            self.list_widget.addItem('{section[0]} - {section[1]}'.format(
                section=section))
        self.list_widget.update()

    @pyqtSlot(int)
    def select_section(self, section_idx):
        self.list_widget.setCurrentRow(section_idx)

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        section_idx = self.list_widget.row(item)
        self.signal_section_selected.emit(section_idx)
