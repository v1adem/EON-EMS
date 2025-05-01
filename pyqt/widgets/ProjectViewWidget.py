import asyncio
from datetime import datetime, timedelta

import logging

import xlsxwriter

from pyqt.SafeButton import SafeButton
from register_maps.RegisterMaps import RegisterMap

logger = logging.getLogger(__name__)

import pytz
from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import Qt, QSize, QTime, QDate
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QHBoxLayout, QMessageBox, QDialog, \
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QDialogButtonBox, QRadioButton, QTimeEdit, QSpacerItem, QSizePolicy, \
    QFileDialog, QDateEdit
from tortoise.exceptions import DoesNotExist

from tools.config import resource_path, get_timezone
from models.Device import Device
from models.Report import SDM120Report, SDM120ReportTmp, SDM630Report, SDM630ReportTmp, SDM72Report, SDM72ReportTmp


class ProjectViewWidget(QWidget):
    def __init__(self, main_window, project):
        super().__init__(main_window)
        self.main_window = main_window
        self.main_window.hide_loading()
        self.project = project
        self.isAdmin = main_window.isAdmin

        layout = QVBoxLayout(self)

        self.loading_indicator = QLabel(self)
        self.loading_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.loading_indicator.setStyleSheet("background: transparent;")
        self.loading_indicator.hide()

        top_layout = QHBoxLayout()

        self.label = QLabel(f"Деталі проєкту: {project.name}")
        self.label.setStyleSheet("font-size: 18px;")
        top_layout.addWidget(self.label)

        export_button = SafeButton("Експорт в Excel")
        export_button.setFixedSize(360, 36)
        export_button.setStyleSheet("font-size: 16px;")
        export_button.clicked.connect(self.open_project_export_dialog)
        top_layout.addWidget(export_button)

        refresh_button = SafeButton()
        refresh_button.setIcon(QIcon(resource_path("pyqt/icons/refresh.png")))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_devices)
        top_layout.addWidget(refresh_button)

        layout.addLayout(top_layout)

        self.devices_list = QListView(self)
        layout.addWidget(self.devices_list)

        self.devices_model = QStandardItemModel()
        self.devices_list.setModel(self.devices_model)

        self.load_devices()

        self.add_device_button = SafeButton("Додати новий пристрій", 1000, self)
        self.add_device_button.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.add_device_button)
        if not self.isAdmin:
            self.add_device_button.setDisabled(True)
        self.add_device_button.clicked.connect(self.add_new_device)

        self.devices_list.doubleClicked.connect(self.open_device_details)

    def load_devices(self):
        self.main_window.show_loading()
        async def run_load_devices():
            self.devices = await Device.filter(project_id=self.project.id).all()
            for index, device in enumerate(self.devices, start=1):
                item = QStandardItem()
                item.setData(device.name, Qt.ItemDataRole.UserRole)
                item.setSizeHint(QSize(0, 60))
                self.devices_model.appendRow(item)

                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)

                number_label = QLabel(f"{index}")
                number_label.setStyleSheet("font-size: 14px; color: #666666;")
                number_label.setFixedWidth(40)
                number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                item_layout.addWidget(number_label)

                name_label = QLabel(device.name)
                name_label.setStyleSheet("font-size: 18px;")
                item_layout.addWidget(name_label)

                def set_status_label():
                    if device.actual_status and device.reading_status:
                        actual_status_label.setText("Підключено")
                        actual_status_label.setStyleSheet("font-size: 18px; color: #00aa00;")
                        time_label.setText("")
                    elif device.reading_status is False:
                        actual_status_label.setText("Вимкнено")
                        time_label.setText("")
                        actual_status_label.setStyleSheet("font-size: 18px; color: #aa0000;")
                    else:
                        actual_status_label.setText(f"Відключено.")
                        local_tz = get_timezone()
                        time_label.setText(f"Наступна спроба - {device.wait_time.astimezone(local_tz).strftime('%H:%M')}")
                        actual_status_label.setStyleSheet("font-size: 18px; color: #aa0000;")

                actual_status_label = QLabel()
                time_label = QLabel()
                time_label.setStyleSheet("font-size: 18px;")
                set_status_label()
                actual_status_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
                actual_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                time_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
                time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item_layout.addWidget(actual_status_label)
                item_layout.addWidget(time_label)

                toggle_status_button = SafeButton("Увімкнути" if not device.get_reading_status() else "Вимкнути")
                toggle_status_button.setFixedSize(100, 36)
                toggle_status_button.clicked.connect(
                    lambda _, d=device, btn=toggle_status_button: AsyncioPySide6.runTask(
                        self.toggle_device_status(d, btn)))

                force_try_button = SafeButton("Примусова спроба")
                force_try_button.setFixedSize(150, 36)
                force_try_button.clicked.connect(
                    lambda _, d=device: AsyncioPySide6.runTask(self.force_device_try(d, time_label)))

                edit_button = SafeButton()
                edit_button.setIcon(QIcon(resource_path("pyqt/icons/edit.png")))
                edit_button.setFixedSize(36, 36)
                edit_button.clicked.connect(lambda _, d=device: self.edit_device(d))

                delete_button = SafeButton()
                delete_button.setIcon(QIcon(resource_path("pyqt/icons/delete.png")))
                delete_button.setFixedSize(36, 36)
                delete_button.clicked.connect(lambda _, d=device: self.delete_device(d))

                if not device.actual_status and device.reading_status:
                    item_layout.addWidget(force_try_button)

                if self.isAdmin:
                    item_layout.addWidget(toggle_status_button)
                    if not device.actual_status and device.reading_status:
                        pass
                    item_layout.addWidget(edit_button)
                    item_layout.addWidget(delete_button)

                    spacer = QSpacerItem(5, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                    item_layout.addSpacerItem(spacer)

                item_layout.setContentsMargins(0, 0, 0, 0)

                self.devices_list.setIndexWidget(item.index(), item_widget)
        try:
            self.devices_model.clear()
            AsyncioPySide6.runTask(run_load_devices())
        finally:
            self.main_window.hide_loading()

    async def toggle_device_status(self, device, button):
        try:
            device.toggle_reading_status()
            await device.save()
            button.setText("Увімкнути" if not device.get_reading_status() else "Вимкнути")
            self.load_devices()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося змінити статус пристрою: {e}",
                                 QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
            logger.error(e)

    async def force_device_try(self, device, time_label):
        try:
            time_label.setText("Відбувається спроба...")
            tz = get_timezone()
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            wait_time_local = now_utc - timedelta(seconds=600)
            device.wait_time = wait_time_local.astimezone(tz)
            await device.save(update_fields=['wait_time'])
            await asyncio.sleep(1)
            await self.load_devices()
        except Exception as e:
            logger.error(e)

    def add_new_device(self):
        self.main_window.show_loading()
        self.new_device = None
        async def run_add_device():
            dialog = QDialog(self)
            dialog.setWindowTitle("Додати новий пристрій")
            form_layout = QFormLayout(dialog)

            device_name_input = QLineEdit(dialog)
            form_layout.addRow("Назва пристрою:", device_name_input)

            manufacturer_input = QComboBox(dialog)
            manufacturer_input.addItem("Eastron")
            form_layout.addRow("Виробник:", manufacturer_input)

            model_input = QComboBox(dialog)
            model_input.addItems(["SDM120", "SDM630", "SDM72"])
            form_layout.addRow("Модель:", model_input)

            device_address_input = QSpinBox(dialog)
            device_address_input.setRange(1, 255)
            form_layout.addRow("Адреса пристрою:", device_address_input)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                       dialog)
            form_layout.addRow(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                device_name = device_name_input.text()
                manufacturer = manufacturer_input.currentText()
                model = model_input.currentText()
                device_address = device_address_input.value()

                existing_device = await Device.filter(name=device_name, project_id=self.project.id).first()
                if existing_device:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою назвою вже існує в проєкті.",
                                        QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
                    return

                existing_address = await Device.filter(device_address=device_address,
                                                       project_id=self.project.id).first()
                if existing_address:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою адресою вже існує в проєкті.",
                                        QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
                    return

                self.new_device = Device(name=device_name, manufacturer=manufacturer, model=model,
                                         device_address=device_address, project_id=self.project.id)
                await self.new_device.save()
                self.edit_device(self.new_device)
        try:
            AsyncioPySide6.runTask(run_add_device())
        finally:
            self.main_window.hide_loading()

    def edit_device(self, device):
        self.main_window.show_loading()
        async def run_save_changes():
            dialog = QDialog(self)
            dialog.setWindowTitle("Редагувати пристрій")
            form_layout = QFormLayout(dialog)

            device_name_input = QLineEdit(dialog)
            device_name_input.setText(device.name)
            form_layout.addRow("Назва пристрою:", device_name_input)

            manufacturer_input = QComboBox(dialog)
            manufacturer_input.addItem("Eastron")
            manufacturer_input.setCurrentText(device.manufacturer)
            manufacturer_input.setEditable(False)
            form_layout.addRow("Виробник:", manufacturer_input)

            model_input = QComboBox(dialog)
            model_input.addItems(["SDM120", "SDM630", "SDM72"])
            model_input.setCurrentText(device.model)
            model_input.setEditable(False)
            form_layout.addRow("Модель:", model_input)

            device_address_input = QSpinBox(dialog)
            device_address_input.setRange(1, 255)
            device_address_input.setValue(device.device_address)
            form_layout.addRow("Адреса пристрою:", device_address_input)

            reading_type_interval = QRadioButton("Інтервал")
            reading_type_time = QRadioButton("Час")
            reading_type_interval.setChecked(device.reading_type == 1)
            reading_type_time.setChecked(device.reading_type == 2)
            form_layout.addRow("Тип зчитування:", reading_type_interval)
            form_layout.addRow("", reading_type_time)

            reading_interval_input = QSpinBox(dialog)
            reading_interval_input.setRange(2, 59)
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

            # Додавання полів для налаштування граничних значень
            minV_input = QSpinBox(dialog)
            minV_input.setRange(1, 99999)
            minV_input.setValue(device.minV)
            form_layout.addRow("Мінімальна напруга (V):", minV_input)

            maxV_input = QSpinBox(dialog)
            maxV_input.setRange(1, 99999)
            maxV_input.setValue(device.maxV)
            form_layout.addRow("Максимальна напруга (V):", maxV_input)

            maxA_input = QSpinBox(dialog)
            maxA_input.setRange(1, 99999)
            maxA_input.setValue(device.maxA)
            form_layout.addRow("Максимальний струм (A):", maxA_input)

            maxW_input = QSpinBox(dialog)
            maxW_input.setRange(1, 99999)  # Потужність у межах 10-10000W
            maxW_input.setValue(device.maxW)
            form_layout.addRow("Максимальна потужність (W):", maxW_input)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                       dialog)
            form_layout.addRow(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_name = device_name_input.text().strip()
                new_manufacturer = manufacturer_input.currentText()
                new_model = model_input.currentText()
                new_device_address = device_address_input.value()

                if reading_type_interval.isChecked():
                    new_reading_type = 1
                    new_reading_interval = reading_interval_input.value() * 60
                    new_reading_time = 0
                elif reading_type_time.isChecked():
                    new_reading_type = 2
                    new_reading_interval = 0
                    new_reading_time = reading_time_input.time().secsTo(QTime(0, 0)) * -1
                else:
                    new_reading_type = device.reading_type
                    new_reading_interval = device.reading_interval
                    new_reading_time = device.reading_time

                # Отримання нових граничних значень
                new_minV = minV_input.value()
                new_maxV = maxV_input.value()
                new_maxA = maxA_input.value()
                new_maxW = maxW_input.value()

                # Оновлення параметрів пристрою
                device.name = new_name
                device.manufacturer = new_manufacturer
                device.model = new_model
                device.device_address = new_device_address
                device.reading_type = new_reading_type
                device.reading_interval = new_reading_interval
                device.reading_time = new_reading_time

                device.minV = new_minV
                device.maxV = new_maxV
                device.maxA = new_maxA
                device.maxW = new_maxW

                await device.save(force_update=True)
                self.load_devices()
        try:
            AsyncioPySide6.runTask(run_save_changes())
        finally:
            self.main_window.hide_loading()

    def delete_device(self, device):
        self.main_window.show_loading()
        async def run_delete_device():
            reply = QMessageBox.question(self, "Підтвердження видалення",
                                         f"Ви впевнені, що хочете видалити пристрій '{device.name}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if device.model == "SDM120":
                        await SDM120Report.filter(device_id=device.id).delete()
                        await SDM120ReportTmp.filter(device_id=device.id).delete()
                    elif device.model == "SDM630":
                        await SDM630Report.filter(device_id=device.id).delete()
                        await SDM630ReportTmp.filter(device_id=device.id).delete()
                    elif device.model == "SDM72":
                        await SDM72Report.filter(device_id=device.id).delete()
                        await SDM72ReportTmp.filter(device_id=device.id).delete()

                    await device.delete()
                    self.load_devices()

                except DoesNotExist:
                    print("Проєкт або пристрої не знайдені в базі даних.")
        try:
            AsyncioPySide6.runTask(run_delete_device())
        finally:
            self.main_window.hide_loading()

    def open_device_details(self, index):
        self.main_window.show_loading()
        async def run_open_device_details():
            device_name = self.devices_model.itemFromIndex(index).data(Qt.ItemDataRole.UserRole)
            device = await Device.filter(name=device_name, project_id=self.project.id).first()
            if device:
                self.main_window.open_device_details(device)
            else:
                print("Пристрій не знайдено.")

        AsyncioPySide6.runTask(run_open_device_details())

    def open_project_export_dialog(self):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("Експорт проєкту в Excel")
        self.dialog.setFixedSize(400, 150)

        layout = QVBoxLayout(self.dialog)

        date_range_layout = QHBoxLayout()
        start_label = QLabel("Початок:")
        self.start_export_date = QDateEdit(QDate.currentDate().addYears(-1))
        self.start_export_date.setCalendarPopup(True)
        end_label = QLabel("Кінець:")
        self.end_export_date = QDateEdit(QDate.currentDate())
        self.end_export_date.setCalendarPopup(True)
        date_range_layout.addWidget(start_label)
        date_range_layout.addWidget(self.start_export_date)
        date_range_layout.addWidget(end_label)
        date_range_layout.addWidget(self.end_export_date)

        layout.addLayout(date_range_layout)

        save_button = SafeButton("Зберегти в Excel")
        save_button.clicked.connect(self.export_project_to_excel)
        layout.addWidget(save_button)

        self.dialog.setLayout(layout)
        self.dialog.exec()

    def export_project_to_excel(self):
        self.main_window.show_loading()
        start_datetime = self.start_export_date.dateTime().toPython()
        end_datetime_for_name = self.end_export_date.dateTime().toPython()
        end_datetime = self.end_export_date.dateTime().addDays(1).toPython()

        async def run_export_to_excel():
            devices = await Device.filter(project_id=self.project.id).all()
            if not devices:
                QMessageBox.warning(self, "Експорт", "У проєкті немає пристроїв для експорту.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Зберегти файл",
                f"{self.project.name}_{start_datetime.date()}_{end_datetime_for_name.date()}.xlsx",
                "Excel Files (*.xlsx)")

            if not file_path:
                return

            try:
                workbook = xlsxwriter.Workbook(file_path)

                for device in devices:
                    if device.model == "SDM120":
                        report_model = SDM120Report
                    elif device.model == "SDM630":
                        report_model = SDM630Report
                    elif device.model == "SDM72":
                        report_model = SDM72Report
                    else:
                        continue

                    report_data = await report_model.filter(
                        device_id=device.id,
                        timestamp__gte=start_datetime,
                        timestamp__lte=end_datetime
                    ).order_by("timestamp").all()

                    if not report_data:
                        continue

                    worksheet = workbook.add_worksheet(device.name)
                    worksheet.write(0, 0, "Дата/Час")

                    register_map = RegisterMap.get_register_map(device.model)
                    column_labels = RegisterMap.get_columns_with_units(register_map)

                    columns = list(column_labels.keys())
                    for col_idx, column in enumerate(columns, start=1):
                        header_text = f"{column} ({column_labels[column]})" if column_labels[column] else column
                        worksheet.write(0, col_idx, header_text)

                    for row_idx, entry in enumerate(report_data, start=1):
                        worksheet.write(row_idx, 0, entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                        for col_idx, column in enumerate(columns, start=1):
                            value = getattr(entry, column, None)
                            worksheet.write(row_idx, col_idx, value)

                    worksheet.set_column(0, len(columns), 20)

                workbook.close()
                QMessageBox.information(self, "Експорт", "Експорт даних в Excel пройшов успішно.")
                self.dialog.accept()

            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Сталася помилка при експорті даних: {e}")
        try:
            AsyncioPySide6.runTask(run_export_to_excel())
        finally:
            self.main_window.hide_loading()
