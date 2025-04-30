from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPushButton


class SafeButton(QPushButton):
    def __init__(self, text="", cooldown_ms=1000, parent=None):
        super().__init__(text, parent)
        self.cooldown_ms = cooldown_ms
        self.clicked.connect(self.disable_temporarily)

    def disable_temporarily(self):
        self.setDisabled(True)
        QTimer.singleShot(self.cooldown_ms, self.setEnabled)