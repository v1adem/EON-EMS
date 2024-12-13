from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox


class LanguageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Зміна мови")
        self.setFixedSize(200, 100)

        layout = QVBoxLayout(self)

        label = QLabel("Виберіть мову:", self)
        layout.addWidget(label)

        self.language_combo = QComboBox(self)
        self.language_combo.addItems(["Українська", "English"])
        layout.addWidget(self.language_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        layout.setContentsMargins(10, 10, 10, 10)

        self.selected_language = self.language_combo.currentText()

    def accept(self):
        self.selected_language = self.language_combo.currentText()
        super().accept()
