from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit

class ConsoleWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.document().setMaximumBlockCount(100)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def write(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if "WARNING" in text:
            color = QColor("yellow")
        elif "ERROR" in text:
            color = QColor("red")
        elif "INFO" in text:
            color = QColor("lime")
        elif "DEBUG" in text:
            color = QColor("skyblue")
        else:
            color = QColor("white")

        format = QTextCharFormat()
        format.setForeground(color)
        cursor.mergeCharFormat(format)
        cursor.insertText(text)

        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def flush(self):
        pass