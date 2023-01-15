from PyQt5.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout, QSizePolicy


class PyMP3GainStatus(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.text = QLabel("")
        self.sub_progress = QProgressBar()
        self.total_progress = QProgressBar()

        layout.addWidget(self.sub_progress)
        layout.addWidget(self.total_progress)
        layout.addWidget(self.text)
        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setSizePolicy(sp)

    def set_progress(self, text, sub_iter, sub_max, total_iter, total_max):
        self.text.setText(text)

        self.sub_progress.setMinimum(0)
        self.sub_progress.setMaximum(sub_max)
        self.sub_progress.setValue(sub_iter)

        self.total_progress.setMinimum(0)
        self.total_progress.setMaximum(total_max)
        self.total_progress.setValue(total_iter)

    def reset_progress(self):
        self.text.setText("")

        self.sub_progress.setMaximum(1)
        self.sub_progress.reset()

        self.total_progress.setMaximum(1)
        self.total_progress.reset()
