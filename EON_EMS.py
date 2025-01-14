import asyncio

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtWidgets import (QApplication)

import sys

from tortoise import Tortoise

from pyqt.MainWindow import MainWindow

async def cleanup():
    await Tortoise.close_connections()

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with AsyncioPySide6.use_asyncio():
        main_window = MainWindow()
        main_window.show()

        try:
            sys.exit(app.exec())
        finally:
            asyncio.run(cleanup())