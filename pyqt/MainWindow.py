import asyncio

from PySide6 import QtCore
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QDialog

from config import resource_path
from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.dialogs.SettingsDialog import SettingsDialog
from pyqt.widgets.DeviceDetailsWidget import DeviceDetailsWidget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm


class MainWindow(QMainWindow):
    def __init__(self, thread_manager):
        super().__init__()

        self.thread_manager = thread_manager

        self.isAdmin = False

        self.setWindowTitle("EON EMS v0.2.2")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.menu_bar = self.menuBar()

        back_icon = QIcon(resource_path("pyqt/icons/back.png"))
        exitAct = QAction(back_icon, "Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.triggered.connect(self.go_back)
        self.toolbar = self.addToolBar("Exit")
        self.toolbar.addAction(exitAct)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(60, 30))

        # Додаємо вкладку "Налаштування" в тулбар
        # settings_icon = QIcon(resource_path("pyqt/icons/settings.png"))
        settings_menu = self.menu_bar.addMenu("Налаштування")
        settings_action = QAction("Час видалення", self) #(settings_icon, "Час видалення", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(settings_action)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)

    def open_settings_dialog(self):
        """Відкриває діалогове вікно для зміни часу видалення."""
        dialog = SettingsDialog(self)
        dialog.exec()

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
        self.project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(self.project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        self.device_details_widget = DeviceDetailsWidget(self, device)
        self.stacked_widget.addWidget(self.device_details_widget)
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
