import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PySide6.QtWidgets import QPlainTextEdit


class ConsoleWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.document().setMaximumBlockCount(100)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFont(QFont("Monospace", 10))
        self.ansi_escape = re.compile(r'\x1b\[[0-9;]*m')

    def write(self, text):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.append_formatted_text(text, cursor)

    def append_formatted_text(self, text, cursor):
        parts = self.ansi_escape.split(text)
        for part in parts:
            if not part:
                continue
            if self.ansi_escape.fullmatch(part):
                self.apply_format(part, cursor)
            else:
                cursor.insertText(part)

        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def apply_format(self, ansi_code, cursor):
        format = QTextCharFormat()
        codes = [int(c) for c in ansi_code[2:-1].split(';') if c]
        if not codes:
            cursor.mergeCharFormat(QTextCharFormat())
            return

        for code in codes:
            if code == 0:
                cursor.mergeCharFormat(QTextCharFormat())
            elif 30 <= code <= 37:
                colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
                if 0 <= code - 30 < len(colors):
                    format.setForeground(QColor(colors[code - 30]))
            elif 90 <= code <= 97:
                colors = ["darkgray", "lightred", "lightgreen", "lightyellow", "lightblue", "lightmagenta", "lightcyan",
                          "white"]
                if 0 <= code - 90 < len(colors):
                    format.setForeground(QColor(colors[code - 90]))
            elif 40 <= code <= 47:
                colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
                if 0 <= code - 40 < len(colors):
                    format.setBackground(QColor(colors[code - 40]))
            elif 1 == code:
                format.setFontWeight(QFont.Weight.Bold)
            elif 2 == code:
                format.setFontWeight(QFont.Weight.Light)
            elif 4 == code:
                format.setFontUnderline(True)
        cursor.mergeCharFormat(format)

    def flush(self):
        pass
