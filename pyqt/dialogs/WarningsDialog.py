import logging

import pytz
from PySide6.QtWidgets import QDialog, QLabel, QComboBox, QDialogButtonBox, QFormLayout, QVBoxLayout, QPushButton

from tools.config import get_timezone, set_timezone, get_warnings, toggle_warnings

logger = logging.getLogger(__name__)


class WarningsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налаштування контролю пікових значень")
        self.setMinimumWidth(350)

        self.layout = QVBoxLayout(self)

        self.status_label = QLabel()
        self.update_ui()

        self.toggle_btn = QPushButton("Змінити статус")
        self.toggle_btn.clicked.connect(self.handle_toggle)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.accept)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.toggle_btn)
        self.layout.addWidget(self.button_box)

    def update_ui(self):
        is_enabled = get_warnings()
        if is_enabled:
            self.status_label.setText("Обробка пікових навантажень увімкнена")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Обробка пікових навантажень вимкнена")
            self.status_label.setStyleSheet("color: red;")

    def handle_toggle(self):
        toggle_warnings()
        self.update_ui()