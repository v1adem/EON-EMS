import logging

from pyqt.widgets.DeviceDetailsWidgets.SDM120DeviceDetailsWidget import SDM120DeviceDetailsWidget
from pyqt.widgets.DeviceDetailsWidgets.SDM630DeviceDetailsWidget import SDM630DeviceDetailsWidget
from pyqt.widgets.DeviceDetailsWidgets.SDM72DeviceDetailsWidget import SDM72DeviceDetailsWidget

logger = logging.getLogger(__name__)

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QAction, QIcon, QMovie
from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QDialog, QSystemTrayIcon, QMenu, \
    QLabel, QPushButton, QWidgetAction

from tools.config import resource_path, toggle_demo_port_status, toggle_peak_power
from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.dialogs.DeletingTimeDialog import DeletingTimeDialog
from pyqt.dialogs.TimezoneDialog import TimezoneDialog
from pyqt.widgets.DeviceDetailsWidgets.BaseDeviceDetailsWidget import BaseDeviceDetailsWidget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm


class MainWindow(QMainWindow):
    def __init__(self, thread_manager):
        super().__init__()

        self.initTrayIcon()
        self.is_exit = False

        self.thread_manager = thread_manager

        self.projects_widget = None
        self.project_view_widget = None
        self.device_details_widget = None

        self.isAdmin = False

        self.setWindowTitle("EON EMS DEMO v0.4.0")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        screen_geometry = QtCore.QRect(QtGui.QGuiApplication.primaryScreen().geometry())
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.menu_bar = self.menuBar()

        back_icon = QIcon(resource_path("pyqt/icons/back.png"))
        exitAct = QAction(back_icon, "Exit", self)
        exitAct.setShortcut("Esc")
        exitAct.triggered.connect(self.go_back)
        self.toolbar = self.addToolBar("Exit")
        self.toolbar.addAction(exitAct)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QtCore.QSize(60, 30))

        # settings_icon = QIcon(resource_path("pyqt/icons/settings.png"))
        settings_menu = self.menu_bar.addMenu("Налаштування")
        settings_action = QAction("Час видалення", self)  # (settings_icon, "Час видалення", self)
        settings_action.triggered.connect(self.open_deleting_time_dialog)
        settings_menu.addAction(settings_action)

        settings_action_timezone = QAction("Часовий пояс", self)
        settings_action_timezone.triggered.connect(self.open_timezone_dialog)
        settings_menu.addAction(settings_action_timezone)

        testing_menu = self.menu_bar.addMenu("🛠 Тестування")
        testing_menu.setStyleSheet("""
            QMenu {
                font-weight: bold;
                color: red;
            }
        """)
        toggle_ports_button = QPushButton("Перемкнути доступність портів")
        toggle_ports_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                color: red;
            }
        """)
        toggle_ports_button.clicked.connect(self.toggle_ports)

        toggle_ports_action = QWidgetAction(self)
        toggle_ports_action.setDefaultWidget(toggle_ports_button)
        testing_menu.addAction(toggle_ports_action)

        toggle_peaks_button = QPushButton("Увімкнути/Вимкнути пікові значення")
        toggle_peaks_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                color: red;
            }
        """)
        toggle_peaks_button.clicked.connect(self.toggle_peak_values)

        toggle_peaks_action = QWidgetAction(self)
        toggle_peaks_action.setDefaultWidget(toggle_peaks_button)
        testing_menu.addAction(toggle_peaks_action)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)

        self.showMaximized()

    def toggle_ports(self):
        toggle_demo_port_status()
        if self.projects_widget is not None:
            self.projects_widget.load_projects()

    def toggle_peak_values(self):
        toggle_peak_power()

    def initTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("pyqt/icons/app-icon.png")))
        self.tray_icon.setVisible(True)

        tray_menu = QMenu()
        exit_action = tray_menu.addAction('Завершити роботу')
        exit_action.triggered.connect(self.exit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_icon_clicked)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showMaximized()
            self.raise_()

    def open_deleting_time_dialog(self):
        dialog = DeletingTimeDialog(self)
        dialog.exec()

    def open_timezone_dialog(self):
        dialog = TimezoneDialog(self)
        dialog.exec()

    def change_language(self):
        language_dialog = LanguageDialog(self)
        if language_dialog.exec_() == QDialog.DialogCode.Accepted:
            current_language = language_dialog.selected_language

    def open_projects_list(self):
        self.projects_widget = ProjectsWidget(self)
        self.stacked_widget.addWidget(self.projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    def open_project_details(self, project):
        self.project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(self.project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        widget_class = {
            "SDM120": SDM120DeviceDetailsWidget,
            "SDM630": SDM630DeviceDetailsWidget,
            "SDM72": SDM72DeviceDetailsWidget,
        }.get(device.model, BaseDeviceDetailsWidget)

        self.device_details_widget = widget_class(self, device)
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
            self.isAdmin = False

            self.stacked_widget.removeWidget(self.registration_widget)

            self.registration_widget = RegistrationLoginForm(self)
            self.stacked_widget.addWidget(self.registration_widget)

            self.stacked_widget.setCurrentIndex(0)

    def show_loading(self):
        self.loading_label = QLabel(self)
        self.loading_label.setStyleSheet("background-color: rgba(255, 255, 255, 200);")
        self.loading_label.setFixedSize(self.size())
        self.loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        movie = QMovie(resource_path("pyqt/animations/loading.gif"))
        self.loading_label.setMovie(movie)
        movie.start()

        self.loading_label.show()

    def hide_loading(self):
        if hasattr(self, 'loading_label') and self.loading_label is not None:
            if self.loading_label.movie() is not None:
                self.loading_label.movie().stop()
            self.loading_label.hide()
            self.loading_label.deleteLater()
            del self.loading_label

    def exit_app(self):
        self.is_exit = True
        QtCore.QCoreApplication.quit()

    def closeEvent(self, event):
        if self.is_exit:
            super().closeEvent(event)
        else:
            self.hide()
            event.ignore()