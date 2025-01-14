import asyncio
import os
import sys
from msilib import init_database

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtAsyncio import QAsyncioEventLoop
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QDialog
from tortoise import Tortoise
from typing_extensions import get_original_bases

from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.widgets.DeviceDetailsWidget import DeviceDetailsWidget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm
from rtu.DataCollector import DataCollector


def get_database_path():
    """
    Визначає шлях до бази даних у каталозі APPDATA (Windows)
    або відповідному каталозі для Linux/MacOS.
    """
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'EON')

    os.makedirs(app_dir, exist_ok=True)

    return os.path.join(app_dir, 'eon.db')


def init_database(db_path):
    """
    Ініціалізує Tortoise ORM і створює таблиці, якщо вони ще не існують.
    """
    async def run_init_database():
        await Tortoise.init(
            db_url=f"sqlite:///{db_path}",
            modules={"models": ["models.Admin", "models.Project", "models.Device", "models.Report"]},
        )
        await Tortoise.generate_schemas(safe=True)

    AsyncioPySide6.runTask(run_init_database())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        init_database(get_database_path())

        #self.data_collectors = []
        #self.timers = []

        #projects = Project.all()

        #for project in projects:
        #    data_collector = DataCollector(project, self)
        #    self.data_collectors.append(data_collector)
        #    timer = QTimer(self)
        #    timer.timeout.connect(data_collector.collect_data)
        #    timer.setInterval(3000)
        #    timer.start()

        #    self.timers.append(timer)


        self.isAdmin = False

        self.setWindowTitle("EON EMS v0.2.2")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.menu_bar = self.menuBar()
        self.menu_bar.setStyleSheet("font-size: 16px;")

        back_action = QAction("Назад", self)
        self.menu_bar.addAction(back_action)
        back_action.triggered.connect(self.go_back)

        #settings_menu = self.menu_bar.addMenu("Налаштування")
        #language_action = QAction("Мова", self)
        #settings_menu.addAction(language_action)
        #language_action.triggered.connect(self.change_language)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)

    def change_language(self):
        language_dialog = LanguageDialog(self)
        if language_dialog.exec_() == QDialog.DialogCode.Accepted:
            current_language = language_dialog.selected_language
            print(f"Мова змінена на: {current_language}")

    def open_projects_list(self):
        self.projects_widget = ProjectsWidget(self)
        self.stacked_widget.addWidget(self.projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    def open_project_details(self, project):
        project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        device_details_widget = DeviceDetailsWidget(self, device)
        self.stacked_widget.addWidget(device_details_widget)
        self.stacked_widget.setCurrentIndex(3)


    def go_back(self):
        current_index = self.stacked_widget.currentIndex()
        self.projects_widget.load_projects()

        if current_index > 0:
            current_widget = self.stacked_widget.currentWidget()
            self.stacked_widget.removeWidget(current_widget)

            self.stacked_widget.setCurrentIndex(current_index - 1)

        if current_index == 1:
            print("Перехід на екран реєстрації/логіну. Очищення даних...")
            self.isAdmin = False

            self.stacked_widget.removeWidget(self.registration_widget)

            self.registration_widget = RegistrationLoginForm(self)
            self.stacked_widget.addWidget(self.registration_widget)

            self.stacked_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        asyncio.get_event_loop().stop()
        super().closeEvent(event)
