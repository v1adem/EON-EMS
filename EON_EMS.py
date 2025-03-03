import asyncio
import os
import sys

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QThreadPool
from PySide6.QtCore import Qt  # Named colors.
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
)

from tortoise import Tortoise

import config
from pyqt.MainWindow import MainWindow
from rtu.DataCollector import DataCollectorRunnable


def get_darkModePalette(app=None):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127), )

    return darkPalette


def get_database_path():
    """
    Визначає шлях до бази даних у каталозі APPDATA (Windows)
    або відповідному каталозі для Linux/MacOS.
    """
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'EON')

    os.makedirs(app_dir, exist_ok=True)

    return os.path.join(app_dir, 'eon.db')


async def init_database(db_path):
    await Tortoise.init(
        db_url=f"sqlite:///{db_path}",
        modules={"models": ["models.Admin", "models.Project", "models.Device", "models.Report"]},
    )
    await Tortoise.generate_schemas(safe=True)

class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.pool = QThreadPool()  # Використовуємо пул потоків

    def add_thread(self, project, main_window):
        if project.id in self.threads:
            print(f"Thread for project {project.id} already exists.")
            return

        task = DataCollectorRunnable(project, main_window)
        self.pool.start(task)
        self.threads[project.id] = task

    def remove_thread(self, project_id):
        task = self.threads.get(project_id)
        if task:
            task.stop_collecting = True  # Встановлюємо прапорець для зупинки збору
            del self.threads[project_id]
            print(f"Task for project {project_id} stopped and removed.")
        else:
            print(f"No task found for project {project_id}.")

    def stop_all_threads(self):
        for project_id in list(self.threads.keys()):
            self.remove_thread(project_id)
        print("All tasks stopped.")


async def initialize_threads(main_window, thread_manager):
    from models.Project import Project

    projects = await Project.all()
    for project in projects:
        thread_manager.add_thread(project, main_window)

def stop_threads_synchronously(thread_manager):
    """Зупиняємо всі потоки в головному потоці."""
    print("Stopping all threads...")
    thread_manager.stop_all_threads()
    print("All threads stopped.")

def on_about_to_quit(loop, thread_manager):
    """Обробник закриття програми."""
    print("Application is about to quit...")

    # Закриваємо всі потоки
    stop_threads_synchronously(thread_manager)
    loop_is_running = False

    # Перевірка на наявність активного циклу подій
    if loop:
        loop_is_running = loop.is_running()

    async def shutdown():
        try:
            print("Closing database connections...")
            await Tortoise.close_connections()

            print("Cancelling all asyncio tasks...")
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            print("All cleanup completed.")
        except Exception as e:
            print(f"Error during shutdown: {e}")

    # Викликаємо завершальні дії
    if loop_is_running:
        loop.call_soon_threadsafe(lambda: asyncio.run(shutdown()))
    else:
        asyncio.run(shutdown())

if __name__ == "__main__":
    # Configuring the application
    config.get_deleting_time()

    db_path = os.path.join(get_database_path())
    asyncio.run(init_database(db_path))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(config.resource_path("pyqt/icons/app-icon.ico")))
    app.setPalette(get_darkModePalette(app))
    thread_manager = ThreadManager()

    with AsyncioPySide6.use_asyncio() as loop:
        main_window = MainWindow(thread_manager)
        main_window.show()

        # ініціалізуємо всі потоки
        AsyncioPySide6.runTask(initialize_threads(main_window, thread_manager))

        # Реєструємо обробник закриття
        app.aboutToQuit.connect(lambda: on_about_to_quit(loop, thread_manager))

        try:
            sys.exit(app.exec())
        except Exception as e:
            print(f"Error during shutdown: {e}")