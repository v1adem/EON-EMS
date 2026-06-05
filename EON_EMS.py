import logging
import os
import sys
import asyncio

from tools import config

config.init_config()
config.init_logger()

logger = logging.getLogger(__name__)

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from tortoise import Tortoise

from pyqt.MainWindow import MainWindow
from tools.ThreadManager import stop_threads_synchronously, ThreadManager, initialize_threads
from tools.start_tools import is_already_running, show_warning_message, get_database_path, init_database, \
    get_darkModePalette


def on_about_to_quit(loop, thread_manager):
    logger.info("Application about to quit. Starting cleanup...")

    stop_threads_synchronously(thread_manager)

    async def shutdown():
        try:
            logger.info("Closing Tortoise ORM database connections...")
            await Tortoise.close_connections()
            logger.info("Database connections successfully closed.")
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")

    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(shutdown(), loop)
    else:
        asyncio.run(shutdown())


if __name__ == "__main__":
    if is_already_running():
        show_warning_message()
        sys.exit(1)

    logger.info('Starting EON EMS Core Engine')

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

        main_window.run_async_task(initialize_threads(main_window, thread_manager))

        app.aboutToQuit.connect(lambda: on_about_to_quit(loop, thread_manager))

        try:
            sys.exit(app.exec())
        except Exception as e:
            logger.error(f"Critical error during main application execution loop: {e}")
