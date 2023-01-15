import copy

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

from gui.ValueEntry import ValueEntry


class PreferencesDialog(QDialog):
    Ok = QDialogButtonBox.Ok
    Cancel = QDialogButtonBox.Cancel

    def __init__(self, preferences=None):
        super().__init__()

        if preferences is None:
            self.preferences = self.get_default_preferences()
        else:
            self.preferences = copy.deepcopy(preferences)

        self.setModal(True)

        self.setWindowTitle("Preferences")

        # Main layout
        central_layout = QVBoxLayout()
        central_layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(central_layout)

        def create_entry(name, label, action=None, data=None):
            entry = ValueEntry(name=name, value=self.preferences[name], description=label, action=action, data=data)
            entry.value_changed.connect(lambda value, x=name: self.update_preference(x, value))
            central_layout.addWidget(entry)
            return entry

        self.default_target_volume = create_entry("default_target_volume", "Default Target Volume:",
                                                  ValueEntry.ActionNone, [89, 119, 1.5])
        self.default_mode = create_entry("default_mode", "Default Mode:",
                                         ValueEntry.ActionList, "Track;Single Album;Album Folders")
        self.max_files = create_entry("max_files", "Maximum # of files per process:",
                                      ValueEntry.ActionNone, [1, 999, 1])
        self.mp3gain_bin = create_entry("mp3gain_bin", "MP3Gain executable:", ValueEntry.ActionFileOpen)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.on_accept)
        self.buttons.rejected.connect(self.on_reject)

        central_layout.addWidget(self.buttons)

    def exec(self):
        super().exec()

        return self.result()

    def on_accept(self):
        self.done(QDialogButtonBox.Ok)

    def on_reject(self):
        self.done(QDialogButtonBox.Cancel)

    def update_preference(self, name, value):
        self.preferences[name] = value

    @staticmethod
    def get_default_preferences():
        preferences = {"mp3gain_bin": "/usr/bin/mp3gain",
                       "default_target_volume": 89.0,
                       "max_files": 99,
                       "default_mode": "Album Folders"}

        return preferences
