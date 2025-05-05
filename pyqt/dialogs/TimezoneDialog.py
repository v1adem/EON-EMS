import logging

import pytz
from PySide6.QtWidgets import QDialog, QLabel, QComboBox, QDialogButtonBox, QFormLayout

from tools.config import get_timezone, set_timezone

logger = logging.getLogger(__name__)


class TimezoneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налаштування часового поясу")
        self.setGeometry(200, 200, 300, 150)

        self.current_timezone = get_timezone()

        self.timezone_label = QLabel("Поточний часовий пояс:")
        self.current_timezone_label = QLabel(str(self.current_timezone))
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems(pytz.all_timezones)
        self.timezone_combo.setCurrentText(str(self.current_timezone))

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QFormLayout()
        layout.addRow(self.timezone_label, self.current_timezone_label)
        layout.addRow("Виберіть новий часовий пояс:", self.timezone_combo)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def accept(self):
        new_timezone_str = self.timezone_combo.currentText()
        if new_timezone_str != str(get_timezone()):
            set_timezone(new_timezone_str)
        super().accept()
