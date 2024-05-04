#!/usr/bin/env python3
import sys
import os
import argparse

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from gui import PyMP3GainApp

VER = "0.2.9"
script_path = os.path.dirname(os.path.abspath(__file__))


def main():
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    arguments = get_arguments().parse_args()

    app = QApplication(sys.argv)

    ex = PyMP3GainApp(VER, arguments.debug)
    exit_code = app.exec_()

    sys.exit(exit_code)


def get_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--debug",
                        action="store_true",
                        dest="debug",
                        help="Debug output.")

    parser.set_defaults()

    return parser


if __name__ == "__main__":
    main()
