import logging

logger = logging.getLogger(__name__)

import asyncio
import os
import sys

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
)
from tortoise import Tortoise

from tools import config
from pyqt.MainWindow import MainWindow
from tools.ThreadManager import stop_threads_synchronously, ThreadManager, initialize_threads
from tools.start_tools import is_already_running, show_warning_message, get_database_path, init_database, \
    get_darkModePalette


def on_about_to_quit(loop, thread_manager):
    stop_threads_synchronously(thread_manager)

    async def shutdown():
        try:
            logger.info("Closing database connections...")
            await Tortoise.close_connections()

            logger.info("Cancelling all asyncio tasks...")
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("All cleanup completed.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    if loop and loop.is_running():
        loop.call_soon_threadsafe(lambda: asyncio.run(shutdown()))
    else:
        asyncio.run(shutdown())


if __name__ == "__main__":

    if is_already_running():
        show_warning_message()
        sys.exit(1)

    config.init_config()
    config.init_logger()

    logger.info('Starting EON EMS')
    db_path = os.path.join(get_database_path())
    asyncio.run(init_database(db_path))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(config.resource_path("pyqt/icons/app-icon.ico")))
    app.setStyle("Fusion")
    app.setPalette(get_darkModePalette(app))
    thread_manager = ThreadManager()

    with AsyncioPySide6.use_asyncio() as loop:
        main_window = MainWindow(thread_manager)
        main_window.show()

        AsyncioPySide6.runTask(initialize_threads(main_window, thread_manager))

        app.aboutToQuit.connect(lambda: on_about_to_quit(loop, thread_manager))

        try:
            sys.exit(app.exec())
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
