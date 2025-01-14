import os
import sys


def resource_path(relative_path):
    """
    Отримує абсолютний шлях до ресурсу, враховуючи упаковку в .exe (PyInstaller).
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


