from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, \
    QStackedWidget, QAction, QDialog

from PyQt5.QtCore import QTimer

from models.Admin import Admin
from models.Project import Project
from pyqt.dialogs.ConnectionDialog import ConnectionDialog
from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.widgets.DeviceDetailsSDM120Widget import DeviceDetailsSDM120Widget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm
from rtu.DataCollector import DataCollector


class MainWindow(QMainWindow):
    def __init__(self, db_session):
        super().__init__()

        self.db_session = db_session
        self.data_collectors = []
        self.timers = []

        projects = self.db_session.query(Project).all()

        for project in projects:
            data_collector = DataCollector(db_session, project, self)
            self.data_collectors.append(data_collector)

            timer = QTimer(self)
            timer.timeout.connect(data_collector.collect_data)
            timer.setInterval(1000)
            timer.start()

            self.timers.append(timer)

        self.db_session = db_session
        self.isAdmin = False

        self.setWindowTitle("EON EMS (SDM120 edition)")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.menu_bar = self.menuBar()
        self.menu_bar.setStyleSheet("font-size: 16px;")

        back_action = QAction("Назад", self)
        self.menu_bar.addAction(back_action)
        back_action.triggered.connect(self.go_back)

        settings_menu = self.menu_bar.addMenu("Налаштування")
        language_action = QAction("Мова", self)
        settings_menu.addAction(language_action)
        language_action.triggered.connect(self.change_language)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)
        admin = self.db_session.query(Admin).first()
        if admin is not None:
            if admin.always_admin is True:
                self.isAdmin = True
                self.open_projects_list()

    def change_language(self):
        language_dialog = LanguageDialog(self)
        if language_dialog.exec_() == QDialog.Accepted:
            current_language = language_dialog.selected_language
            print(f"Мова змінена на: {current_language}")

    def open_connection_dialog(self):
        dialog = ConnectionDialog(self)
        dialog.exec_()

    def open_projects_list(self):
        self.projects_widget = ProjectsWidget(self)
        self.stacked_widget.addWidget(self.projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    def open_project_details(self, project):
        project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        if device.model == "SDM120":
            device_details_widget = DeviceDetailsSDM120Widget(self, device)
            self.stacked_widget.addWidget(device_details_widget)
            self.stacked_widget.setCurrentIndex(3)
        elif device.model == "SDM630":
            pass


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
