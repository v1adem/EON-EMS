from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtWidgets import QApplication
import asyncio
import os
import sys

from tortoise import Tortoise

from pyqt.MainWindow import MainWindow
from rtu.DataCollectorTest import DataCollectorThread


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


async def cleanup():
    await Tortoise.close_connections()

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class ThreadManager:
    def __init__(self):
        self.threads = {}  # Зберігаємо посилання на потоки, ключ — ідентифікатор проєкту

    def add_thread(self, project, main_window):
        if project.id in self.threads:
            print(f"Thread for project {project.id} already exists.")
            return

        thread = DataCollectorThread(project, main_window)
        thread.start()
        self.threads[project.id] = thread

    def remove_thread(self, project_id):
        thread = self.threads.get(project_id)
        if thread:
            thread.quit()
            thread.wait()
            del self.threads[project_id]
            print(f"Thread for project {project_id} stopped and removed.")
        else:
            print(f"No thread found for project {project_id}.")

    def stop_all_threads(self):
        for project_id in list(self.threads.keys()):
            self.remove_thread(project_id)
        print("All threads stopped.")


async def initialize_threads(main_window, thread_manager):
    from models.Project import Project

    projects = await Project.all()
    for project in projects:
        thread_manager.add_thread(project, main_window)


if __name__ == "__main__":
    db_path = os.path.join(get_database_path())
    asyncio.run(init_database(db_path))

    app = QApplication(sys.argv)
    thread_manager = ThreadManager()

    with AsyncioPySide6.use_asyncio():
        main_window = MainWindow(thread_manager)
        main_window.show()

        AsyncioPySide6.runTask(initialize_threads(main_window, thread_manager))

        try:
            sys.exit(app.exec())
        finally:
            thread_manager.stop_all_threads()
            asyncio.run(cleanup())
