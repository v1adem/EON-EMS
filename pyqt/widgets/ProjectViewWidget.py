from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QPushButton, QMessageBox, \
    QHBoxLayout, QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QSpinBox, QRadioButton, QTimeEdit, \
    QCheckBox
from PyQt5.QtCore import Qt, QSize, QTime

from config import resource_path
from models.Device import Device


class ProjectViewWidget(QWidget):
    def __init__(self, main_window, project):
        super().__init__(main_window)
        self.main_window = main_window
        self.project = project
        self.db_session = main_window.db_session
        self.isAdmin = main_window.isAdmin

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Деталі проєкту: {project.name}")
        layout.addWidget(self.label)

        self.devices_list = QListView(self)
        layout.addWidget(self.devices_list)

        self.devices_model = QStandardItemModel()
        self.devices_list.setModel(self.devices_model)

        self.load_devices()

        self.add_device_button = QPushButton("Додати новий пристрій", self)
        self.add_device_button.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.add_device_button)
        if not self.isAdmin:
            self.add_device_button.setDisabled(True)
        self.add_device_button.clicked.connect(self.add_new_device)

        self.devices_list.doubleClicked.connect(self.open_device_details)

    def load_devices(self):
        self.devices_model.clear()
        devices = self.db_session.query(Device).filter_by(project_id=self.project.id).all()

        for index, device in enumerate(devices, start=1):
            item = QStandardItem()
            item.setData(device.name, Qt.UserRole)
            item.setSizeHint(QSize(0, 60))
            self.devices_model.appendRow(item)

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)

            # Порядковий номер
            number_label = QLabel(f"{index}")  # Номер по порядку
            number_label.setStyleSheet("font-size: 14px; color: #666666;")
            number_label.setFixedWidth(40)  # Ширина для номера
            number_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(number_label)

            name_label = QLabel(device.name)
            name_label.setStyleSheet("font-size: 18px;")
            item_layout.addWidget(name_label)

            toggle_status_button = QPushButton("Увімкнути" if not device.get_reading_status() else "Вимкнути")
            toggle_status_button.setFixedSize(100, 36)
            toggle_status_button.clicked.connect(
                lambda _, d=device, btn=toggle_status_button: self.toggle_device_status(d, btn))

            edit_button = QPushButton()
            edit_button.setIcon(QIcon(resource_path("pyqt/icons/edit.png")))
            edit_button.setFixedSize(36, 36)
            edit_button.clicked.connect(lambda _, d=device: self.edit_device(d))


            delete_button = QPushButton()
            delete_button.setIcon(QIcon(resource_path("pyqt/icons/delete.png")))
            delete_button.setFixedSize(36, 36)
            delete_button.clicked.connect(lambda _, d=device: self.delete_device(d))
            if self.isAdmin:
                item_layout.addWidget(toggle_status_button)
                item_layout.addWidget(edit_button)
                item_layout.addWidget(delete_button)

            item_layout.setContentsMargins(0, 0, 0, 0)

            self.devices_list.setIndexWidget(item.index(), item_widget)

    def toggle_device_status(self, device, button):
        try:
            device.toggle_reading_status()
            self.db_session.commit()
            button.setText("Увімкнути" if not device.get_reading_status() else "Вимкнути")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося змінити статус пристрою: {e}")

    def add_new_device(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Додати новий пристрій")
            form_layout = QFormLayout(dialog)

            device_name_input = QLineEdit(dialog)
            form_layout.addRow("Назва пристрою:", device_name_input)

            manufacturer_input = QComboBox(dialog)
            manufacturer_input.addItem("Eastron")
            form_layout.addRow("Виробник:", manufacturer_input)

            model_input = QComboBox(dialog)
            model_input.addItems(["SDM120", "SDM630"])
            form_layout.addRow("Модель:", model_input)

            device_address_input = QSpinBox(dialog)
            device_address_input.setRange(1, 255)
            form_layout.addRow("Адреса пристрою:", device_address_input)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            form_layout.addRow(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.Accepted:
                device_name = device_name_input.text()
                manufacturer = manufacturer_input.currentText()
                model = model_input.currentText()
                device_address = device_address_input.value()

                existing_device = self.db_session.query(Device).filter_by(name=device_name,
                                                                          project_id=self.project.id).first()
                if existing_device:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою назвою вже існує в проєкті.")
                    return

                existing_address = self.db_session.query(Device).filter_by(device_address=device_address,
                                                                           project_id=self.project.id).first()
                if existing_address:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою адресою вже існує в проєкті.")
                    return

                new_device = Device(name=device_name, manufacturer=manufacturer, model=model,
                                    device_address=device_address, project_id=self.project.id)
                self.db_session.add(new_device)
                self.db_session.commit()

                self.load_devices()

                self.edit_device(new_device)
        except Exception as e:
            print(f"Помилка при додаванні пристрою: {e}")
            QMessageBox.critical(self, "Помилка", "Не вдалося додати пристрій.")

    def edit_device(self, device):
        dialog = QDialog(self)
        dialog.setWindowTitle("Редагувати пристрій")
        form_layout = QFormLayout(dialog)

        # Поле для зміни назви
        device_name_input = QLineEdit(dialog)
        device_name_input.setText(device.name)
        form_layout.addRow("Назва пристрою:", device_name_input)

        # Вибір виробника
        manufacturer_input = QComboBox(dialog)
        manufacturer_input.addItem("Eastron")
        manufacturer_input.setCurrentText(device.manufacturer)
        manufacturer_input.setEditable(False)
        form_layout.addRow("Виробник:", manufacturer_input)

        # Вибір моделі
        model_input = QComboBox(dialog)
        model_input.addItems(["SDM120", "SDM630"])
        model_input.setCurrentText(device.model)
        model_input.setEditable(False)
        form_layout.addRow("Модель:", model_input)

        # Адреса пристрою
        device_address_input = QSpinBox(dialog)
        device_address_input.setRange(1, 255)
        device_address_input.setValue(device.device_address)
        form_layout.addRow("Адреса пристрою:", device_address_input)

        # Тип зчитування
        reading_type_interval = QRadioButton("Інтервал")
        reading_type_time = QRadioButton("Час")
        reading_type_interval.setChecked(device.reading_type == 1)
        reading_type_time.setChecked(device.reading_type == 2)
        form_layout.addRow("Тип зчитування:", reading_type_interval)
        form_layout.addRow("", reading_type_time)

        # Інтервал або час зчитування
        reading_interval_input = QSpinBox(dialog)
        reading_interval_input.setRange(1, 1440)
        reading_interval_input.setValue(device.reading_interval // 60)  # В хвилинах
        if device.reading_type == 2:
            reading_interval_input.setDisabled(True)
        form_layout.addRow("Інтервал зчитування (хв):", reading_interval_input)

        reading_time_input = QTimeEdit(dialog)
        reading_time_input.setDisplayFormat("HH:mm")
        reading_time_input.setTime(QTime(0, 0).addSecs(device.reading_time))
        if device.reading_type == 1:
            reading_time_input.setDisabled(True)
        form_layout.addRow("Час зчитування:", reading_time_input)

        reading_type_interval.toggled.connect(
            lambda: reading_interval_input.setEnabled(reading_type_interval.isChecked()))
        reading_type_time.toggled.connect(lambda: reading_time_input.setEnabled(reading_type_time.isChecked()))

        label = QLabel("Параметри для збору інформації:")
        form_layout.addRow(label)

        # Параметри для зчитування з одиницями вимірювання
        parameters_checkboxes = []
        parameter_units = {
            "voltage": "V",
            "current": "A",
            "frequency": "Hz",
            "active_power": "W",
            "total_active_energy": "kWh"
        }

        parameter_pairs = device.get_parameter_pairs()

        for param, unit in parameter_units.items():
            checkbox = QCheckBox(f"{param} ({unit})")
            checkbox.setChecked(
                any(p[0] == param and p[1] == unit for p in parameter_pairs))
            form_layout.addRow(checkbox)
            parameters_checkboxes.append((param, unit, checkbox))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        form_layout.addRow(buttons)

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() == QDialog.Accepted:
            device.name = device_name_input.text()
            device.manufacturer = manufacturer_input.currentText()
            device.model = model_input.currentText()
            device.device_address = device_address_input.value()
            device.reading_type = 1 if reading_type_interval.isChecked() else 2
            device.reading_interval = reading_interval_input.value() * 60 if reading_type_interval.isChecked() else 0
            device.reading_time = reading_time_input.time().secsTo(
                QTime(0, 0)) * -1 if reading_type_time.isChecked() else 0

            selected_parameters = [
                f"{param}:{unit}" for param, unit, checkbox in parameters_checkboxes if checkbox.isChecked()
            ]
            device.parameters = ','.join(selected_parameters)

            self.db_session.commit()
            self.load_devices()

    def delete_device(self, device):
        reply = QMessageBox.question(self, "Підтвердження видалення",
                                     f"Ви впевнені, що хочете видалити пристрій '{device.name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_session.delete(device)
            self.db_session.commit()
            self.load_devices()

    def open_device_details(self, index):
        device_name = self.devices_model.itemFromIndex(index).data(Qt.UserRole)
        device = self.db_session.query(Device).filter_by(name=device_name, project_id=self.project.id).first()
        if device:
            self.main_window.open_device_details(device)
        else:
            print("Пристрій не знайдено.")
