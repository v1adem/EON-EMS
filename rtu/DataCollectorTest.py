import asyncio
import random
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QThread
from PySide6.QtWidgets import QMessageBox

from models.Device import Device
from models.Report import SDM120Report, SDM120ReportTmp


class DataCollectorThread(QThread):
    def __init__(self, project, main_window):
        super().__init__()
        self.project = project
        self.main_window = main_window
        self.collector = DataCollectorTest(self.project, main_window)  # Ваш клас збору даних

    def run(self):
        """Запуск асинхронного завдання в окремому потоці."""
        loop = asyncio.new_event_loop()  # Створення нового циклу подій
        asyncio.set_event_loop(loop)  # Встановлюємо цей цикл як поточний

        loop.run_until_complete(self.collector.collect_data())


class DataCollectorTest(QObject):
    def __init__(self, project, main_window):
        super().__init__()
        self.main_window = main_window
        self.project = project
        self.stop_collecting = False  # Прапорець для зупинки циклу

    async def collect_data(self):
        while not self.stop_collecting:  # Безкінечний цикл
            devices = await Device.filter(project=self.project).all()
            for device in devices:
                if not device.reading_status:
                    continue

                if device.model == "SDM120":
                    await self.collect_data_sdm120(device)
                else:
                    QMessageBox.warning(
                        self.main_window, f"{device.name}", f"{device.model} - Невідома модель")

            await asyncio.sleep(1)

    async def collect_data_sdm120(self, device):
        last_report = await SDM120Report.filter(device=device).first()
        print("Читається девайс: " + device.name + " / З проєкту " + self.project.name)
        new_data = {
            "line_voltage_1": random.randrange(210, 250),
            "current_1": random.randrange(10, 50),
            "active_power_1": 50,
            "power_1": 60,
            "reactive_power_1": 50,
            "power_factor": 1,
            "frequency": 50,
            "import_active_energy_1": 0,
            "export_active_energy_1": 0,
            "total_active_energy": 0,
            "total_reactive_energy": 0,
            "total_kWh_1": 120
        }

        tmp_report_data = {
            "device_id": device.id,
            "line_voltage_1": new_data.get("line_voltage_1"),
            "current_1": new_data.get("current_1"),
            "power_1": new_data.get("power_1"),
            "total_active_energy": new_data.get("total_active_energy"),
            "total_reactive_energy": new_data.get("total_reactive_energy")
        }

        tmp_report = SDM120ReportTmp(**tmp_report_data)
        await tmp_report.save()

        tmp_reports = await SDM120ReportTmp.all()

        if len(tmp_reports) > 1:
            await tmp_reports[0].delete()

        if last_report:
            device_reading_interval = device.reading_interval - 10
            if device.reading_type == 2:
                reading_time = device.reading_time
                start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if datetime.now() < (
                        start_of_day + timedelta(minutes=reading_time)) or last_report.timestamp >= start_of_day:
                    return

            if last_report.timestamp.replace(tzinfo=None) + timedelta(seconds=device_reading_interval) > datetime.now():
                return

        report_data = {
            "device_id": device.id,
        }
        report_data.update({key: value for key, value in new_data.items() if value is not None})

        new_report = SDM120Report(**report_data)
        await new_report.save()