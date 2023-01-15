import queue
import time

from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QAction, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QApplication

from lib.util import *

FILE_COLUMN = 0
FOLDER_COLUMN = 1
VOLUME_COLUMN = 2
GAIN_DB_COLUMN = 3
GAIN_MP3_COLUMN = 4
CLIPPING_COLUMN = 5
ALBUM_GAIN_DB_COLUMN = 6
TAG_INFO_COLUMN = 7
FILENAME_COLUMN = 8


class PyMP3List(QTableWidget):
    process_done = QtCore.pyqtSignal(str, name="process_done")
    process_progress = QtCore.pyqtSignal(str, int, int, name="process_progress")
    mp3gain_progress = QtCore.pyqtSignal(str, int, int, int, int, name="mp3gain_progress")

    def __init__(self, parent, target_volume=89.0, mp3gain=None):
        super().__init__(0, 9, parent)

        self.setHorizontalHeaderItem(FILE_COLUMN, QTableWidgetItem("File"))
        self.setHorizontalHeaderItem(FOLDER_COLUMN, QTableWidgetItem("Folder"))
        self.setHorizontalHeaderItem(VOLUME_COLUMN, QTableWidgetItem("Volume"))
        self.setHorizontalHeaderItem(GAIN_DB_COLUMN, QTableWidgetItem("Gain (dB)"))
        self.setHorizontalHeaderItem(GAIN_MP3_COLUMN, QTableWidgetItem("Gain (mp3)"))
        self.setHorizontalHeaderItem(CLIPPING_COLUMN, QTableWidgetItem("Clipping"))
        self.setHorizontalHeaderItem(ALBUM_GAIN_DB_COLUMN, QTableWidgetItem("Album gain (dB)"))
        self.setHorizontalHeaderItem(TAG_INFO_COLUMN, QTableWidgetItem("Tag Info"))
        self.setHorizontalHeaderItem(FILENAME_COLUMN, QTableWidgetItem("$file"))

        self.setSelectionBehavior(QHeaderView.SelectRows)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        self.setEditTriggers(self.NoEditTriggers)

        header = self.horizontalHeader()
        header.resizeSections(QHeaderView.ResizeToContents)
        header.setSectionHidden(8, True)
        header.setStretchLastSection(True)

        self.mp3_list = dict()
        self.base_volume = 89.0
        self.target_volume = target_volume
        self.album_analysis = False
        self.album_by_folder = False
        self.mp3gain = mp3gain
        self.mp3gain_bin = self.mp3gain.mp3gain

        self.process_thread = None

    def add_mp3(self, mp3_file):
        if mp3_file in self.mp3_list:
            return

        working_file = Path(mp3_file)

        file = str(working_file.name)
        folder = str(working_file.parent.name)

        current_row = self.rowCount()
        self.insertRow(self.rowCount())

        self.mp3_list[mp3_file] = current_row

        self.setItem(current_row, FILE_COLUMN, QTableWidgetItem(file))
        self.setItem(current_row, FOLDER_COLUMN, QTableWidgetItem(folder))
        self.setItem(current_row, FILENAME_COLUMN, QTableWidgetItem(mp3_file))

        result = self.mp3gain.get_file_analysis(mp3_file, stored_only=True, block=True)
        analysis = result[0]

        self.update_row_by_file(mp3_file, analysis)
        self.resizeColumnsToContents()

    def update_row_by_file(self, mp3, analysis):
        try:
            row = self.mp3_list[mp3]
        except KeyError:
            print("Error updating row:")
            print(mp3)
            print(analysis)
            return

        self.setItem(row, TAG_INFO_COLUMN, QTableWidgetItem(str(analysis["tag_exists"])))

        if analysis["tag_exists"]:
            mp3_gain_value = analysis["MP3 gain"] + self.get_gain_offset()
            volume = self.base_volume + -1 * analysis.get("dB gain", 0)
            gain_db = mp3_gain_value * 1.5
            album_db_gain = analysis.get("Album dB gain", None)

            volume = "{:.2f}".format(volume)
            self.setItem(row, VOLUME_COLUMN, QTableWidgetItem(volume))
            self.setItem(row, GAIN_DB_COLUMN, QTableWidgetItem(str(gain_db)))
            self.setItem(row, GAIN_MP3_COLUMN, QTableWidgetItem(str(mp3_gain_value)))
            self.setItem(row, ALBUM_GAIN_DB_COLUMN, QTableWidgetItem(str(album_db_gain)))

            if analysis["Max Amplitude"] > 32767:
                self.setItem(row, CLIPPING_COLUMN, QTableWidgetItem("Yes"))
                self.color_row(row, (255, 0, 0))
            else:
                self.setItem(row, CLIPPING_COLUMN, QTableWidgetItem(""))
                self.color_row(row, (0, 0, 0))
        else:
            self.setItem(row, VOLUME_COLUMN, QTableWidgetItem(""))
            self.setItem(row, GAIN_DB_COLUMN, QTableWidgetItem(""))
            self.setItem(row, GAIN_MP3_COLUMN, QTableWidgetItem(""))
            self.setItem(row, CLIPPING_COLUMN, QTableWidgetItem(""))
            self.setItem(row, ALBUM_GAIN_DB_COLUMN, QTableWidgetItem(""))
            self.color_row(row, (0, 0, 0))

    def color_row(self, row, color):
        for col in range(self.columnCount()):
            self.item(row, col).setForeground(QBrush(QColor(color[0], color[1], color[2])))

    def set_target_volume(self, target_volume):
        self.target_volume = target_volume

    def set_analysis_config(self, album_analysis, album_by_folder):
        self.album_analysis = album_analysis
        self.album_by_folder = album_by_folder

    def refresh_list(self, mp3_list=None):
        if mp3_list is None:
            mp3_list = self.get_mp3s(by_folder=False)["all"]

        results = self.mp3gain.get_file_analysis(mp3_list, stored_only=True, block=True)

        for result in results:
            self.update_row_by_file(result["File"], result)

    def process_list(self, album_analysis=False, album_analysis_by_folder=False, operation="read", selected_only=False):
        self.setDisabled(True)
        expected_num_results = 0
        start_time = time.time()

        mp3_list = self.get_mp3s(album_analysis_by_folder, selected_only)

        total_files = 0
        for folder in mp3_list:
            total_files = total_files + len(mp3_list[folder])
        total_idx = 0

        if operation not in ["read", "analyze", "apply_gain", "undo_gain", "delete_tags"]:
            raise NotImplementedError

        for idx, folder in enumerate(mp3_list):
            progress_text = "Processed"
            if operation == "apply_gain":
                progress_text = "Applying gain to"
                expected_num_results = self.mp3gain.set_volume(src=mp3_list[folder],
                                                               volume=self.target_volume,
                                                               use_album_gain=album_analysis)
            elif operation == "analyze":
                progress_text = "Analyzing"
                expected_num_results = self.mp3gain.get_file_analysis(src=mp3_list[folder],
                                                                      stored_only=False,
                                                                      album_analysis=album_analysis)
            elif operation == "read":
                progress_text = "Reading"
                expected_num_results = self.mp3gain.get_file_analysis(src=mp3_list[folder],
                                                                      stored_only=True,
                                                                      album_analysis=album_analysis)
            elif operation == "undo_gain":
                progress_text = "Undoing gain on"
                expected_num_results = self.mp3gain.undo_gain(src=mp3_list[folder])
            elif operation == "delete_tags":
                progress_text = "Deleting tags from"
                expected_num_results = self.mp3gain.delete_tags(src=mp3_list[folder])

            result = []
            entry_idx = 0
            num_entries = len(mp3_list[folder])

            while self.mp3gain.is_running():
                try:
                    entry = self.mp3gain.get_result(timeout=0.01)

                    prg_txt = "({}/{}) {} \'{}\'".format(entry_idx + 1, expected_num_results,
                                                         progress_text, clip_text(entry["File"], 128))
                    if len(mp3_list) > 1:
                        self.mp3gain_progress.emit(prg_txt, entry_idx, num_entries, total_idx, total_files)
                    else:
                        self.mp3gain_progress.emit(prg_txt, entry_idx, num_entries, 0, 0)

                    self.update_row_by_file(entry["File"], entry)

                    entry_idx = entry_idx + 1
                    total_idx = total_idx + 1

                    result.append(entry)
                except queue.Empty:
                    QApplication.processEvents()

            if operation in ["analyze", "apply_gain", "undo_gain", "delete_tags"]:
                self.refresh_list(mp3_list[folder])

        total_time = time_as_display(time.time() - start_time)
        if operation == "analyze":
            msg = "Analyzed {} files.".format(total_idx)
        elif operation == "apply_gain":
            msg = "Applied gain to {} files.".format(total_idx)
        elif operation == "undo_gain":
            msg = "Gain undone for {} files.".format(total_idx)
        elif operation == "delete_tags":
            msg = "Deleted tags from {} files.".format(total_idx)
        else:
            msg = "Processed {} files.".format(total_idx)

        msg = msg + " ({})".format(total_time)

        self.process_done.emit(msg)
        self.setDisabled(False)

    def apply_gain_list(self, selected_only=False):
        self.process_list(album_analysis=self.album_analysis, album_analysis_by_folder=self.album_by_folder,
                          operation="apply_gain", selected_only=selected_only)

    def analyze_list(self, selected_only=False):
        self.process_list(album_analysis=self.album_analysis, album_analysis_by_folder=self.album_by_folder,
                          operation="analyze", selected_only=selected_only)

    def undo_gain_list(self):
        self.process_list(album_analysis=False, album_analysis_by_folder=False,
                          operation="undo_gain")

    def delete_tags_list(self):
        self.process_list(album_analysis=False, album_analysis_by_folder=False,
                          operation="delete_tags")

    def get_mp3s(self, by_folder=False, selected_only=False):
        mp3_folders = dict()

        self.mp3_list = dict()

        rows = range(0, self.rowCount())

        for row in rows:
            self.mp3_list[self.item(row, FILENAME_COLUMN).text()] = row

        if selected_only:
            mp3_list = []
            indexes = self.selectedIndexes()
            for index in indexes:
                if index.column() == 0:
                    row = index.row()
                    mp3_list.append(self.item(row, FILENAME_COLUMN).text())
        else:
            mp3_list = self.mp3_list

        for mp3_file in mp3_list:
            mp3 = Path(mp3_file)
            if by_folder:
                folder = str(mp3.parent)
            else:
                folder = "all"

            if folder not in mp3_folders.keys():
                mp3_folders[folder] = []

            mp3_folders[folder].append(mp3_file)

        return mp3_folders

    def get_gain_offset(self):
        db_gain = self.target_volume - self.base_volume
        gain_offset = round(db_gain / 1.5)

        return gain_offset

    def analyze_selected(self):
        self.analyze_list(selected_only=True)

    def remove_selected(self):
        selected_indexes = self.selectedIndexes()

        rows = []

        for index in selected_indexes:
            row = index.row()
            if row not in rows:
                rows.append(row)

        for row in sorted(rows, reverse=True):
            self.removeRow(row)

        _ = self.get_mp3s()  # refresh the mp3list/row lookup table

    def on_context_menu(self, pos):
        menu = QMenu(self)

        analyze_selected = QAction("Analyze selected files", self)
        analyze_selected.triggered.connect(self.analyze_selected)
        menu.addAction(analyze_selected)

        remove_selected = QAction("Remove selected files", self)
        remove_selected.triggered.connect(self.remove_selected)
        menu.addAction(remove_selected)

        menu.popup(self.viewport().mapToGlobal(pos))

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.key() == QtCore.Qt.Key_Delete:
            self.remove_selected()
