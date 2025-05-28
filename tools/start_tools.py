import os
import sys

import logging

from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

import psutil
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from tortoise import Tortoise


def is_already_running():
    count = 0
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'EON_EMS_demo.exe':
            count += 1
    return count > 2


def show_warning_message():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText("Додаток вже запущено!")
    msg.setWindowTitle("Попередження")
    msg.exec()


def get_darkModePalette(app=None):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127), )

    return darkPalette


def get_database_path():
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'EON')

    os.makedirs(app_dir, exist_ok=True)

    return os.path.join(app_dir, 'eon_demo.db')


async def init_database(db_path):
    await Tortoise.init(
        db_url=f"sqlite:///{db_path}",
        modules={"models": ["models.Admin", "models.Project", "models.Device", "models.Report"]},
    )
    await Tortoise.generate_schemas(safe=True)
