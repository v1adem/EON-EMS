import logging
import asyncio
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class DataBridge(QObject):
    # Сигнал передає: (int(project_id), int(device_id), dict(new_data))
    device_data_received = Signal(int, int, dict)
    # Сигнал зміни статусу пристрою: (int(device_id), bool(is_online), str(next_retry_time))
    device_status_changed = Signal(int, bool, str)

data_bridge = DataBridge()


class ThreadManager:
    def __init__(self):
        self.tasks = {}

    def add_thread(self, project, main_window):
        if project.id in self.tasks:
            logger.warning(f"Task for project {project.id} already running.")
            return

        from rtu.DataCollector import collect_data_for_project

        # Створюємо чистий asyncio Task в межах головного event loop
        loop = asyncio.get_event_loop()
        task = loop.create_task(collect_data_for_project(project))
        self.tasks[project.id] = task
        logger.info(f"Async task for project {project.id} started.")

    def remove_thread(self, project_id):
        task = self.tasks.get(project_id)
        if task:
            task.cancel()
            del self.tasks[project_id]
            logger.info(f"Async task for project {project_id} cancelled.")
        else:
            logger.warning(f"No task found for project {project_id}.")

    def stop_all_threads(self):
        for project_id in list(self.tasks.keys()):
            self.remove_thread(project_id)
        logger.info("All async tasks stopped.")


async def initialize_threads(main_window, thread_manager):
    from models.Project import Project

    projects = await Project.all()
    for project in projects:
        thread_manager.add_thread(project, main_window)


def stop_threads_synchronously(thread_manager):
    logger.info("Stopping all manager tasks...")
    thread_manager.stop_all_threads()