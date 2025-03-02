import asyncio
from datetime import datetime, timedelta

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QRunnable
from PySide6.QtWidgets import QMessageBox

from config import get_deleting_time
from models.Device import Device
from models.Report import SDM120Report, SDM120ReportTmp, SDM630Report, SDM72DReport, SDM630ReportTmp, SDM72DReportTmp
from rtu.DataCollectorTestingTools import get_test_data
from rtu.SerialReaderRS485 import SerialReaderRS485


async def get_data_from_device(device, project, main_window):
    try:
        print(f"{device.name} - Reading started")
        client = SerialReaderRS485(device.name, device.model, project.port, device.device_address, project.baudrate,
                                   project.bytesize, project.parity, project.stopbits, main_window)
        return await client.read_all_properties()
    except Exception as e:
        QMessageBox.warning(main_window, "Помилка зчитування", f"{device.name} - {e}",
                            QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)


class DataCollectorRunnable(QRunnable):
    def __init__(self, project, main_window):
        super().__init__()
        self.project = project
        self.main_window = main_window
        self.stop_collecting = False

    def run(self):
        AsyncioPySide6.runTask(self.collect_data())

    async def collect_data(self):
        while not self.stop_collecting:
            devices = await Device.filter(project=self.project).all()
            for device in devices:
                if not device.reading_status:
                    continue
                main_db_model, tmp_db_model = self.get_db_model(device)

                last_report = await main_db_model.filter(device=device).last()
                print(f"Читається девайс: {device.name} Моделі: {device.model} / З проєкту {self.project.name}")
                new_data = await get_data_from_device(device, self.project, self.main_window)

                #new_data = get_test_data(device.model, last_report)
                print(f"Нові дані: {new_data}")

                if new_data == {}:
                    continue

                tmp_report_data = self.get_tmp_data(device, new_data)

                # Перевірка на існування tmp звіту для даного девайсу
                existing_tmp_report = await tmp_db_model.filter(device_id=device.id).first()

                if existing_tmp_report:
                    # Оновлюємо існуючий запис
                    for key, value in tmp_report_data.items():
                        setattr(existing_tmp_report, key, value)
                    await existing_tmp_report.save()
                else:
                    # Створюємо новий запис
                    tmp_report = tmp_db_model(**tmp_report_data)
                    await tmp_report.save()

                if last_report:
                    device_reading_interval = device.reading_interval
                    last_report_time = last_report.timestamp.replace(tzinfo=None)
                    calculated_time = last_report_time + timedelta(seconds=device_reading_interval)
                    current_time = datetime.now().replace(tzinfo=None)

                    if device.reading_type == 2:
                        reading_time = device.reading_time
                        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                        if current_time < (
                                start_of_day + timedelta(minutes=reading_time)) or last_report_time >= start_of_day:
                            continue

                    if calculated_time > current_time:
                        continue

                report_data = {
                    "device_id": device.id,
                }
                report_data.update({key: value for key, value in new_data.items() if value is not None})

                new_report = main_db_model(**report_data)
                await new_report.save()

                # Отримуємо дату, до якої потрібно зберігати звіти
                deleting_time = get_deleting_time()
                if deleting_time > 0:
                    delete_before_date = datetime.now().replace(tzinfo=None) - timedelta(days=deleting_time)

                    # Отримуємо найстаріший звіт
                    first_report = await main_db_model.filter(device=device).first()

                    # Перевіряємо, чи він був створений раніше, ніж delete_before_date, і видаляємо його
                    if first_report and first_report.timestamp.replace(tzinfo=None) < delete_before_date:
                        await first_report.delete()

            await asyncio.sleep(1)

    def get_tmp_data(self, device, new_data):
        if device.model == "SDM120":
            tmp_report_data = {
                "device_id": device.id,
                "line_voltage_1": new_data.get("line_voltage_1"),
                "current_1": new_data.get("current_1"),
                "power_1": new_data.get("power_1"),
                "total_active_energy": new_data.get("total_active_energy"),
                "total_reactive_energy": new_data.get("total_reactive_energy")
            }
            return tmp_report_data
        elif device.model == "SDM630":
            tmp_report_data = {
                "device_id": device.id,
                "line_voltage_1": new_data.get("line_voltage_1"),
                "line_voltage_2": new_data.get("line_voltage_2"),
                "line_voltage_3": new_data.get("line_voltage_3"),
                "current_1": new_data.get("current_1"),
                "current_2": new_data.get("current_2"),
                "current_3": new_data.get("current_3"),
                "power_1": new_data.get("power_1"),
                "power_2": new_data.get("power_2"),
                "power_3": new_data.get("power_3"),
                "total_kWh_1": new_data.get("total_kWh_1"),
                "total_kWh_2": new_data.get("total_kWh_2"),
                "total_kWh_3": new_data.get("total_kWh_3"),
                "total_kWh": new_data.get("total_kWh"),
            }
            return tmp_report_data
        elif device.model == "SDM72D":
            tmp_report_data = {
                "device_id": device.id,
                "line_voltage_1": new_data.get("line_voltage_1"),
                "line_voltage_2": new_data.get("line_voltage_2"),
                "line_voltage_3": new_data.get("line_voltage_3"),
                "current_1": new_data.get("current_1"),
                "current_2": new_data.get("current_2"),
                "current_3": new_data.get("current_3"),
                "power_1": new_data.get("power_1"),
                "power_2": new_data.get("power_2"),
                "power_3": new_data.get("power_3"),
                "total_kWh": new_data.get("total_kWh"),
            }
            return tmp_report_data
        else:
            QMessageBox.warning(
                self.main_window, f"{device.name}", f"{device.model} - Невідома модель", QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel)

    def get_db_model(self, device):
        if device.model == "SDM120":
            return SDM120Report, SDM120ReportTmp
        elif device.model == "SDM630":
            return SDM630Report, SDM630ReportTmp
        elif device.model == "SDM72D":
            return SDM72DReport, SDM72DReportTmp
        else:
            QMessageBox.warning(
                self.main_window, f"{device.name}", f"{device.model} - Невідома модель", QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel)
