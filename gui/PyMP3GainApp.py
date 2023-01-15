import os
import json

from lib.util import *

from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QAction, QFileDialog, \
    QSizePolicy, QHBoxLayout, QGroupBox, QProgressDialog, QMessageBox

from gui.PyMP3List import PyMP3List
from gui.ValueEntry import ValueEntry
from gui.PyMP3GainStatus import PyMP3GainStatus
from gui.PreferencesDialog import PreferencesDialog

from lib.MP3Gain import MP3Gain

PREF_DIR = os.path.expanduser("~/.config/pymp3gain/")
PREF_FILE = "pymp3gain.conf"
PREFERENCES = str(Path(PREF_DIR) / Path(PREF_FILE))


class PyMP3GainApp(QMainWindow):
    def __init__(self, version="unversioned", debug_output=False):
        super().__init__()

        self.debug_output = debug_output
        self.version = version
        self.last_path = ""

        self.preferences = self.load_preferences()
        default_target_volume = self.preferences["default_target_volume"]
        default_mode = self.preferences["default_mode"]
        mp3gain_bin = self.preferences["mp3gain_bin"]
        max_files = self.preferences["max_files"]

        self.mp3gain = MP3Gain(mp3gain_bin=mp3gain_bin, max_files=max_files)

        menu = self.create_menu()

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        def create_frame(widget, title):
            box = QGroupBox(title)
            box.setSizePolicy(widget.sizePolicy())
            layout = QVBoxLayout()
            box.setLayout(layout)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(widget)
            return box

        self.control_pane = QWidget()
        self.control_pane_layout = QHBoxLayout()
        self.control_pane.setLayout(self.control_pane_layout)
        sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.control_pane.setSizePolicy(sp)
        self.main_layout.addWidget(create_frame(self.control_pane, "Controls"), QtCore.Qt.AlignRight)

        self.target_volume = ValueEntry("volume", 89.0, "Target Volume (dB):", data=[89, 119, 1.5])
        self.control_pane_layout.addWidget(self.target_volume, QtCore.Qt.AlignRight)
        self.mp3gain_mode = ValueEntry("mode", default_mode, "Mode:",
                                       action=ValueEntry.ActionList, data="Track;Single Album;Album Folders")
        self.control_pane_layout.addWidget(self.mp3gain_mode, QtCore.Qt.AlignRight)

        self.album_mode = False
        self.album_mode_by_folder = False
        self.mp3gain_mode.value_changed.connect(self.on_mode_changed)

        self.target_volume.set_value(default_target_volume)
        self.mp3gain_mode.set_value(default_mode)

        self.mp3_list = PyMP3List(parent=self, target_volume=default_target_volume, mp3gain=self.mp3gain)
        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.mp3_list.setSizePolicy(sp)
        self.main_layout.addWidget(create_frame(self.mp3_list, "Files"))

        self.target_volume.value_changed.connect(self.mp3_list.set_target_volume)

        self.status = PyMP3GainStatus()
        self.status.reset_progress()
        self.main_layout.addWidget(create_frame(self.status, None))
        self.mp3_list.process_done.connect(self.on_process_done)
        self.mp3_list.mp3gain_progress.connect(self.status.set_progress)

        self.status_bar = self.statusBar()

        self.on_mode_changed(default_mode)

        self.setWindowTitle("PyMP3Gain")
        self.setGeometry(0, 0, 800, 600)

        self.showMaximized()

    def create_menu(self):
        def create_action(parent, parent_menu, name, slot):
            action = QAction(name, parent)
            action.triggered.connect(slot)
            parent_menu.addAction(action)

        menu = self.menuBar()

        menu_file = menu.addMenu("&File")
        create_action(self, menu_file, "Add file...", self.on_menu_file_add_file)
        create_action(self, menu_file, "Add directory...", self.on_menu_file_add_directory)
        menu_file.addSeparator()
        create_action(self, menu_file, "E&xit", self.on_menu_file_exit)

        menu_edit = menu.addMenu("&Edit")
        create_action(self, menu_edit, "Preferences...", self.on_menu_edit_preferences)

        menu_tools = menu.addMenu("&Tools")
        create_action(self, menu_tools, "Apply gain", self.on_menu_tools_apply_gain)
        create_action(self, menu_tools, "Analyze", self.on_menu_tools_analyze)
        menu_tools.addSeparator()
        create_action(self, menu_tools, "Undo gain", self.on_menu_tools_undo)
        create_action(self, menu_tools, "Delete stored tags", self.on_menu_tools_delete)

        menu_help = menu.addMenu("&Help")
        create_action(self, menu_help, "About", self.on_menu_help_about)
        create_action(self, menu_help, "About Qt", self.on_menu_help_about_qt)

        return menu

    def on_menu_file_add_directory(self):
        self.on_menu_file_add_file(True)

    def on_menu_file_add_file(self, directory=False):
        file_type_string = "MP3 files (*.mp3)"

        if directory:
            res = QFileDialog.getExistingDirectory(self, "Open directory...", self.last_path)
        else:
            res, _ = QFileDialog.getOpenFileName(self, "Open file...", self.last_path, file_type_string)

        if res != "":
            self.last_path = res
            if directory:
                self.load_source(sorted(get_paths(res, "mp3", True)))
            else:
                self.load_source([res])

    def on_menu_file_exit(self):
        self.close()

    def on_menu_edit_preferences(self):
        dialog = PreferencesDialog(self.preferences)
        if dialog.exec() == PreferencesDialog.Ok:
            self.preferences = dialog.preferences
            self.save_preferences(self.preferences)
            self.target_volume.set_value(self.preferences["default_target_volume"])
            self.mp3gain_mode.set_value(self.preferences["default_mode"])
            self.mp3gain.set_mp3gain_bin(self.preferences["mp3gain_bin"])
            self.mp3gain.set_max_files(self.preferences["max_files"])

    def on_menu_tools_apply_gain(self):
        self.mp3_list.apply_gain_list()

    def on_menu_tools_analyze(self):
        self.mp3_list.analyze_list()

    def on_menu_tools_undo(self):
        self.mp3_list.undo_gain_list()

    def on_menu_tools_delete(self):
        self.mp3_list.delete_tags_list()

    def on_menu_help_about(self):
        description = "PyMP3Gain is a Qt frontend for mp3gain, written in Python.\n\nmp3gain version: {}".format(
            self.mp3gain.get_version())
        QMessageBox().about(self, "About PyMP3Gain-{}".format(self.version), description)

    def on_menu_help_about_qt(self):
        QMessageBox().aboutQt(self, "PyMP3Gain-{}".format(self.version))

    def on_mode_changed(self, mode):
        if mode == "Track":
            self.album_mode = False
            self.album_mode_by_folder = False
        elif mode == "Single Album":
            self.album_mode = True
            self.album_mode_by_folder = False
        elif mode == "Album Folders":
            self.album_mode = True
            self.album_mode_by_folder = True

        self.mp3_list.set_analysis_config(album_analysis=self.album_mode,
                                          album_by_folder=self.album_mode_by_folder)

    def on_process_done(self, msg=None):
        self.status.reset_progress()
        if msg:
            self.status_bar.showMessage(msg, 4000)

    def load_source(self, src):
        progress_dialog = QProgressDialog("Adding files...", "Cancel", 0, len(src), self)
        progress_dialog.setWindowTitle("Adding Files")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        progress_dialog.setValue(0)

        for item in src:
            if progress_dialog.wasCanceled():
                break

            self.mp3_list.add_mp3(item)

            progress_dialog.setLabelText(clip_text(item, 64))
            progress_dialog.setValue(progress_dialog.value() + 1)

        progress_dialog.setValue(progress_dialog.maximum())
        progress_dialog.deleteLater()

        self.status_bar.showMessage("Loaded {} files.".format(self.mp3_list.rowCount()), 4000)

    def load_preferences(self):
        preferences = PreferencesDialog.get_default_preferences()

        try:
            infile = open(PREFERENCES, 'r')
            preferences_in = json.load(infile)
            if preferences_in.keys() == preferences.keys():
                preferences = preferences_in
            else:
                print("Error loading preferences; using defaults.")
        except FileNotFoundError:
            print("Preferences ({}) not found; using defaults.".format(PREFERENCES))
            if not os.path.exists(PREF_DIR):
                os.makedirs(PREF_DIR)

            self.save_preferences(preferences)

        return preferences

    def save_preferences(self, preferences):
        try:
            outfile = open(PREFERENCES, 'w')
            json.dump(preferences, outfile, indent=4, sort_keys=True)
            outfile.close()
        except IOError:
            print("Error writing preferences ({}).".format(PREFERENCES))
