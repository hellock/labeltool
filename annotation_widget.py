from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import *


class AnnotationWidget(QWidget):
    tube_selected = pyqtSignal(int)

    def __init__(self):
        super(AnnotationWidget, self).__init__()
        # recode the position in the list widget of each tube info
        self.tube_row = dict()
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
        word = self.lineedit_word.text().strip()
        if word == '':
            return
        if self.combobox_word.findText(word) < 0:
            self.combobox_word.addItem(word)
        self.combobox_word.setCurrentText(word)
        self.combobox_word.currentTextChanged.emit(word)
        self.lineedit_word.setText('')

    @pyqtSlot(list)
    def show_tubes(self, tubes):
        """show a list of tube info
        format: {id: label: start-end}
        """
        self.list_widget.clear()
        self.tube_row = dict()
        idx = 0
        for tube in tubes:
            item_str = '{id}: {label}: {start}-{end}'.format(**tube)
            self.list_widget.addItem(item_str)
            self.tube_row[tube['id']] = idx
            idx += 1
        self.list_widget.update()
        # add words in annotations to combobox
        unique_labels = set()
        for tube in tubes:
            unique_labels.add(tube['label'])
        self.set_words(list(unique_labels))

    @pyqtSlot(dict)
    def add_tube(self, tube_info):
        """add or modify the tube info to the list widget
        """
        item_str = '{id}: {label}: {start}-{end}'.format(**tube_info)
        tube_id = tube_info['id']
        if tube_id not in self.tube_row:
            self.list_widget.addItem(item_str)
            self.tube_row[tube_id] = self.list_widget.count() - 1
        else:
            self.list_widget.item(self.tube_row[tube_id]).setText(item_str)

    @pyqtSlot(QListWidgetItem)
    def on_item_double_clicked(self, item):
        tube_info = item.text().split(':')
        tube_id = int(tube_info[0])
        self.combobox_word.setCurrentText(tube_info[1])
        self.tube_selected.emit(tube_id)
