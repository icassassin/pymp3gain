from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QLineEdit, QComboBox, \
    QFileDialog, QCheckBox, QPushButton, QSpinBox, QDoubleSpinBox, QSizePolicy, QPlainTextEdit


class ValueEntry(QWidget):
    ActionNone = 0
    ActionFileOpen = 1
    ActionFileSave = 2
    ActionDirOpen = 4
    ActionList = 8
    ActionMultiline = 16

    value_changed = QtCore.pyqtSignal(object, name="value_changed")

    def __init__(self, name, value, description, action=ActionNone, data=None):
        super().__init__()

        self.name = name
        self.value = value
        self.description = description
        self.action = action

        self.get_value = None
        self.set_value = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if isinstance(value, bool):
            entry = QCheckBox()
            entry.setChecked(value)
            self.get_value = entry.isChecked
            self.set_value = entry.setChecked
            entry.stateChanged.connect(self.on_value_changed)
        elif isinstance(value, int):
            entry = QSpinBox()
            if data is None:
                entry.setRange(-99999999, 99999999)
            else:
                entry.setRange(data[0], data[1])
                if len(data) > 2:
                    entry.setSingleStep(data[2])
            entry.setValue(value)
            self.get_value = entry.value
            self.set_value = entry.setValue
            entry.valueChanged.connect(self.on_value_changed)
        elif isinstance(value, float):
            entry = QDoubleSpinBox()
            if data is None:
                entry.setRange(-99999999, 99999999)
            else:
                entry.setRange(data[0], data[1])
                if len(data) > 2:
                    entry.setSingleStep(data[2])
            entry.setValue(value)
            self.get_value = entry.value
            self.set_value = entry.setValue
            entry.valueChanged.connect(self.on_value_changed)
        else:
            if self.action & self.ActionList == self.ActionList:
                entry = QComboBox()
                entry.addItems(data.split(";"))
                entry.setCurrentText(value)
                self.get_value = entry.currentText
                self.set_value = entry.setCurrentText
                entry.currentTextChanged.connect(self.on_value_changed)
            elif self.action & self.ActionMultiline == self.ActionMultiline:
                entry = QPlainTextEdit()
                entry.setPlainText(value)
                self.get_value = entry.toPlainText
                self.set_value = entry.setPlainText
                entry.textChanged.connect(self.on_value_changed)
            else:
                entry = QLineEdit()
                entry.setText(value)
                self.get_value = entry.text
                self.set_value = entry.setText
                entry.editingFinished.connect(self.on_value_changed)

        entry.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))

        label = QLabel(description)
        label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        layout.addWidget(label, QtCore.Qt.AlignLeft)
        layout.addWidget(entry, QtCore.Qt.AlignLeft)

        if self.action != self.ActionNone:
            if self.action & self.ActionFileSave == self.ActionFileSave:
                button = QPushButton("File")
                button.setMaximumWidth(32)
                button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
                button.clicked.connect(lambda state, x=entry, y=data: self.on_save(x, y))
                layout.addWidget(button, QtCore.Qt.AlignLeft)
            if self.action & self.ActionFileOpen == self.ActionFileOpen:
                button = QPushButton("File")
                button.setMaximumWidth(32)
                button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
                button.clicked.connect(lambda state, x=entry, y=False, z=data: self.on_open(x, y, z))
                layout.addWidget(button, QtCore.Qt.AlignLeft)
            if self.action & self.ActionDirOpen == self.ActionDirOpen:
                button = QPushButton("Dir")
                button.setMaximumWidth(32)
                button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
                button.clicked.connect(lambda state, x=entry, y=True, z=data: self.on_open(x, y, z))
                layout.addWidget(button, QtCore.Qt.AlignLeft)

    def on_open(self, widget, directory=False, file_types=None):
        file_type_string = "(*)"

        if file_types is None:
            file_types = []

        for extension in file_types:
            file_type_string = file_type_string + ";;{} files (*.{})".format(extension.upper(), extension)

        if directory:
            res = QFileDialog.getExistingDirectory(self, "Open directory...", widget.text())
        else:
            res, _ = QFileDialog.getOpenFileName(self, "Open file...", widget.text(), file_type_string)

        if res != "":
            widget.setText(res)

    def on_save(self, widget, file_types=None):
        file_type_string = "(*)"

        if file_types is None:
            file_types = []

        for extension in file_types:
            file_type_string = file_type_string + ";;{} files (*.{})".format(extension.upper(), extension)

        res, _ = QFileDialog.getSaveFileName(self, "Save file...", widget.text(), file_type_string)

        if res != "":
            widget.setText(res)

    def on_value_changed(self):
        self.value_changed.emit(self.get_value())
