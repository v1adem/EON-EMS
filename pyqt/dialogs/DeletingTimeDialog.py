from PySide6.QtWidgets import QDialog, QLabel, QSpinBox, QPushButton, QVBoxLayout, QFormLayout
import logging

logger = logging.getLogger(__name__)
from tools.config import get_deleting_time, set_deleting_time


class DeletingTimeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налаштування часу видалення")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        description = QLabel(
            "Час видалення визначає, через скільки днів дані будуть автоматично видалені."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(1)
        self.days_spinbox.setMaximum(365)
        self.days_spinbox.setValue(get_deleting_time())

        form_layout = QFormLayout()
        form_layout.addRow("Час видалення (днів):", self.days_spinbox)
        layout.addLayout(form_layout)

        save_button = QPushButton("Зберегти")
        save_button.clicked.connect(self.save_deleting_time)
        layout.addWidget(save_button)

    def save_deleting_time(self):
        new_time = self.days_spinbox.value()
        set_deleting_time(new_time)
        self.accept()
