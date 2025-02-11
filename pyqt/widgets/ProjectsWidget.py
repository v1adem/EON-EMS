from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItemModel, QIcon, QStandardItem
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListView, QPushButton, QComboBox, QSizePolicy, \
    QInputDialog, QMessageBox, QDialog, QLineEdit, QSpinBox, QDialogButtonBox, QSpacerItem, QFormLayout
from pymodbus.client import ModbusSerialClient
from tortoise.exceptions import DoesNotExist

from config import resource_path
from models.Device import Device
from models.Project import Project
from models.Report import SDM120Report, SDM120ReportTmp, SDM630Report, SDM630ReportTmp, SDM72DReport, SDM72DReportTmp


class ProjectsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        self.thread_manager = main_window.thread_manager
        self.isAdmin = main_window.isAdmin
        self.setWindowTitle("Список проєктів")

        self.layout = QVBoxLayout(self)

        self.top_layout = QHBoxLayout(self)

        self.projects_label = QLabel("Проєкти", self)
        self.projects_label.setStyleSheet("font-size: 18px;")
        self.top_layout.addWidget(self.projects_label)

        self.projects_list = QListView(self)
        self.projects_model = QStandardItemModel()

        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_projects())
        self.top_layout.addWidget(refresh_button)

        self.layout.addLayout(self.top_layout)

        self.layout.addWidget(self.projects_list)
        self.projects_list.setModel(self.projects_model)
        self.projects_list.doubleClicked.connect(self.open_project_details)

        self.add_project_button = QPushButton("Додати новий проєкт", self)
        self.add_project_button.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.add_project_button)

        if not self.isAdmin:
            self.add_project_button.setDisabled(True)

        self.add_project_button.clicked.connect(self.add_new_project)

    def load_projects(self):
        self.projects_model.clear()

        async def run_load_projects():
            self.projects = await Project.all()
            for index, project in enumerate(self.projects, start=1):
                item = QStandardItem()
                item.setData(project.name, Qt.ItemDataRole.UserRole)
                item.setSizeHint(QSize(0, 60))
                self.projects_model.appendRow(item)

                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)

                # Порядковий номер
                number_label = QLabel(f"{index}")
                number_label.setStyleSheet("font-size: 14px; color: #666666;")
                number_label.setFixedWidth(40)
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(number_label)

                name_label = QLabel(project.name)
                name_label.setStyleSheet("font-size: 18px;")
                item_layout.addWidget(name_label)

                port_combo = QComboBox()
                port_combo.addItems([str(i) for i in range(1, 256)])
                port_combo.setCurrentText(str(project.port))
                port_combo.setFixedWidth(48)
                port_combo.setStyleSheet("font-size: 18px;")
                port_combo.currentIndexChanged.connect(
                    lambda _, p=project, combo=port_combo:
                    self.change_project_port(p, combo.currentText())
                )

                connection_label = QLabel()
                self.update_connection_status(project, connection_label)
                connection_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
                connection_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item_layout.addWidget(connection_label)

                edit_button = QPushButton()
                edit_button.setIcon(QIcon(resource_path("pyqt/icons/edit.png")))
                edit_button.setFixedSize(36, 36)
                edit_button.clicked.connect(lambda _, p=project: self.edit_project(p))

                delete_button = QPushButton()
                delete_button.setIcon(QIcon(resource_path("pyqt/icons/delete.png")))
                delete_button.setFixedSize(36, 36)
                delete_button.clicked.connect(lambda _, p=project: self.delete_project(p))

                if self.isAdmin:
                    item_layout.addWidget(port_combo)
                    item_layout.addWidget(edit_button)
                    item_layout.addWidget(delete_button)

                    spacer = QSpacerItem(5, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                    item_layout.addSpacerItem(spacer)
                else:
                    port_label = QLabel(f"{project.port}")
                    port_label.setStyleSheet("font-size: 18px; border: 0px solid #cccccc; margin: 0px;")
                    item_layout.addWidget(port_label)

                item_layout.setContentsMargins(0, 0, 0, 0)

                self.projects_list.setIndexWidget(item.index(), item_widget)
        AsyncioPySide6.runTask(run_load_projects())

    def update_connection_status(self, project, label):
        if self.is_connected(project):
            label.setText("✅ З'єднання успішне | Порт:")
            label.setStyleSheet(
                "color: green; font-size: 18px; alignment: right; margin: 0px; padding: 0px; border: 0px solid #cccccc;")
        else:
            label.setText("❌ Немає з'єднання | Порт:")
            label.setStyleSheet(
                "color: red; font-size: 18px; alignment: right; margin: 0px; padding: 0px; border: 0px solid #cccccc;")

    def change_project_port(self, project, new_port):
        async def run_change_port():
            project.port = int(new_port)
            await project.save(force_update=True)

            self.load_projects()

        AsyncioPySide6.runTask(run_change_port())

    def is_connected(self, project):
        client = ModbusSerialClient(
            port=f"COM{project.port}",
            baudrate=project.baudrate,
            parity=project.parity,
            stopbits=project.stopbits,
            bytesize=project.bytesize,
        )
        if client.connect():
            client.close()
            return True
        return False

    def add_new_project(self):
        self.new_project = None
        async def run_add_new_project():
            project_name, ok = QInputDialog.getText(self, "Додати новий проєкт", "Введіть назву проєкту:")

            if ok and project_name:
                existing_project = await Project.filter(name=project_name).first()
                if existing_project:
                    QMessageBox.warning(self, "Помилка", "Проєкт з такою назвою вже існує.")
                    return

                self.new_project = Project(name=project_name, port=1)
                await self.new_project.save()

                self.thread_manager.add_thread(self.new_project, self.main_window)
                print(f"Project {self.new_project.name} created and thread started.")

                self.edit_project(self.new_project)

        AsyncioPySide6.runTask(run_add_new_project())

    def delete_project(self, project):
        async def run_delete_project():
            reply = QMessageBox.question(self, "Підтвердження видалення",
                                         f"Ви впевнені, що хочете видалити проєкт '{project.name}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    devices = await Device.filter(project_id=project.id)

                    for device in devices:
                        if device.model == "SDM120":
                            await SDM120Report.filter(device_id=device.id).delete()
                            await SDM120ReportTmp.filter(device_id=device.id).delete()
                        elif device.model == "SDM630":
                            await SDM630Report.filter(device_id=device.id).delete()
                            await SDM630ReportTmp.filter(device_id=device.id).delete()
                        elif device.model == "SDM72D":
                            await SDM72DReport.filter(device_id=device.id).delete()
                            await SDM72DReportTmp.filter(device_id=device.id).delete()

                        await device.delete()

                    await project.delete()
                    self.load_projects()

                    self.thread_manager.remove_thread(project, self.main_window)

                except DoesNotExist:
                    print("Проєкт або пристрої не знайдені в базі даних.")

        AsyncioPySide6.runTask(run_delete_project())

    def edit_project(self, project):
        dialog = QDialog(self)
        dialog.setWindowTitle("Редагувати проєкт")
        layout = QVBoxLayout(dialog)

        # Інформаційний блок
        info_label = QLabel(
            "Усі параметри проєкту мають збігатися з налаштуваннями на пристроях і з налаштуваннями "
            "серійного порту Вашого ПК до якого підключений перетворювач."
            "\nНЕ ВИКОРИСТОВУЙТЕ СИСТЕМНІ ПОРТИ (Зазвичай COM3 та COM4), це може призвести до помилок"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        def open_device_manager():
            import os
            import platform

            if platform.system() == "Windows":
                os.system("start devmgmt.msc")
            else:
                QMessageBox.information(
                    self, "Недоступно", "Функція доступна лише на Windows."
                )

        open_settings_button = QPushButton("Подивитися налаштування порту")
        open_settings_button.clicked.connect(open_device_manager)
        layout.addWidget(open_settings_button)

        # Основна форма
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        # Поля форми
        name_edit = QLineEdit(project.name)
        form_layout.addRow("Назва проєкту:", name_edit)

        description_edit = QLineEdit(project.description or "")
        form_layout.addRow("Опис:", description_edit)

        baudrate_edit = QComboBox()
        baudrate_options = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        baudrate_edit.addItems(map(str, baudrate_options))
        baudrate_edit.setCurrentText(str(project.baudrate))
        form_layout.addRow("Baudrate:", baudrate_edit)

        bytesize_edit = QSpinBox()
        bytesize_edit.setRange(5, 8)
        bytesize_edit.setValue(project.bytesize)
        form_layout.addRow("Bytesize:", bytesize_edit)

        stopbits_edit = QComboBox()
        stopbits_edit.addItems(["1", "1.5", "2"])
        stopbits_edit.setCurrentText(str(project.stopbits))
        form_layout.addRow("Stopbits:", stopbits_edit)

        parity_edit = QComboBox()
        parity_edit.addItems(["N", "E", "O"])  # None, Even, Odd
        parity_edit.setCurrentText(project.parity)
        form_layout.addRow("Parity:", parity_edit)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # Обробка результатів діалогу
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            async def run_save_changes():
                new_name = name_edit.text().strip()
                new_description = description_edit.text().strip()
                new_baudrate = int(baudrate_edit.currentText())
                new_bytesize = bytesize_edit.value()
                new_stopbits = float(stopbits_edit.currentText())
                new_parity = parity_edit.currentText()

                if new_name != project.name:
                    existing_project = await Project.filter(name=new_name).first()
                    if existing_project:
                        QMessageBox.warning(self, "Помилка", "Проєкт з такою назвою вже існує.")
                        return

                project.name = new_name
                project.description = new_description
                project.baudrate = new_baudrate
                project.bytesize = new_bytesize
                project.stopbits = new_stopbits
                project.parity = new_parity

                await project.save(force_update=True)
                self.load_projects()

            AsyncioPySide6.runTask(run_save_changes())

    def open_project_details(self, index):
        async def run_open_details():
            project_name = self.projects_model.itemFromIndex(index).data(Qt.ItemDataRole.UserRole)
            project = await Project.filter(name=project_name).first()
            if project:
                self.main_window.open_project_details(project)
            else:
                print("Couldn't find project")

        AsyncioPySide6.runTask(run_open_details())
