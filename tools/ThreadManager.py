import logging
logger = logging.getLogger(__name__)

from PySide6.QtCore import QThreadPool
from rtu.DataCollector import DataCollectorRunnable


class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.pool = QThreadPool()

    def add_thread(self, project, main_window):
        if project.id in self.threads:
            logger.warning(f"Thread for project {project.id} already exists.")
            return

        task = DataCollectorRunnable(project, main_window)
        self.pool.start(task)
        self.threads[project.id] = task

    def remove_thread(self, project_id):
        task = self.threads.get(project_id)
        if task:
            task.stop_collecting = True
            del self.threads[project_id]
            logger.info(f"Task for project {project_id} stopped and removed.")
        else:
            logger.warning(f"No task found for project {project_id}.")

    def stop_all_threads(self):
        for project_id in list(self.threads.keys()):
            self.remove_thread(project_id)
        logger.info("All tasks stopped.")
        self.pool.waitForDone()

async def initialize_threads(main_window, thread_manager):
    from models.Project import Project

    projects = await Project.all()
    for project in projects:
        thread_manager.add_thread(project, main_window)

def stop_threads_synchronously(thread_manager):
    logger.info("Stopping all threads...")
    thread_manager.stop_all_threads()
    logger.info("All threads stopped.")