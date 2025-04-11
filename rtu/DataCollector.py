import asyncio
from datetime import datetime, timedelta
import logging

from models.Project import Project
from rtu.DataCollectorTestingTools import get_test_data

logger = logging.getLogger(__name__)

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QRunnable
from PySide6.QtWidgets import QMessageBox

from tools.config import get_deleting_time, get_timezone
from models.Device import Device
from models.Report import SDM120Report, SDM120ReportTmp, SDM630Report, SDM72Report, SDM630ReportTmp, SDM72ReportTmp
from rtu.SerialReaderRS485 import SerialReaderRS485


async def get_data_from_device(device, project, main_window):
    try:
        client = SerialReaderRS485(device.name, device.model, project.port, device.device_address, project.baudrate,
                                   project.bytesize, project.parity, project.stopbits, main_window)
        if main_window.thread_manager.threads.get(project.id).stop_collecting:
            return {}
        return await client.read_all_properties()
    except asyncio.CancelledError:
        logger.warning(f"{device.name} - Task cancelled")
        return {}
    except Exception as e:
        logger.warning(f"{device.name} - Task failed: {e}")
        QMessageBox.warning(main_window, "Reading Error", f"{device.name} - {e}",
                            QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)
        return {}


def is_voltage_out_of_range(new_data, device, phase):
    voltage_key = f"line_voltage_{phase}"
    voltage_value = new_data.get(voltage_key)

    if voltage_key in new_data:
        if voltage_value > device.maxV:
            logger.warning(f"Voltage of {phase} phase in {device.name} ({device.model}) is above ({device.maxV}V). \n" +
                  f"Current value: {voltage_value}V. Extra: {voltage_value - device.maxV}V.")
            return True
        elif voltage_value < device.minV:
            if voltage_value == 0:
                return False
            print(f"Voltage of {phase} phase in {device.name} ({device.model}) is less than ({device.minV}V). \n" +
                  f"Current value: {voltage_value}V. Lack: {device.minV - voltage_value}V.")
            return True
    return False


def is_current_over_limit(new_data, device, phase):
    current_key = f"current_{phase}"
    current_value = new_data.get(current_key)

    if current_key in new_data:
        if current_value > device.maxA:
            logger.warning(f"Current of {phase} phase in {device.name} ({device.model}) is above ({device.maxA}A). \n" +
                  f"Current value: {current_value}A. Extra: {current_value - device.maxA}A.")
            return True
    return False


def is_power_over_limit(new_data, device, phase):
    power_key = f"power_{phase}"
    power_value = new_data.get(power_key)

    if power_key in new_data:
        if power_value > device.maxW:
            logger.warning(f"Power of {phase} phase in {device.name} ({device.model}) is above ({device.maxW}W). \n" +
                  f"Current value: {power_value}W. Extra: {power_value - device.maxW}W.")
            return True
    return False


class DataCollectorRunnable(QRunnable):
    def __init__(self, project, main_window):
        super().__init__()
        self.project = project
        self.port = self.project.port
        self.phases = []
        self.main_window = main_window
        self.stop_collecting = False

    def run(self):
        AsyncioPySide6.runTask(self.collect_data())

    async def collect_data(self):
        while not self.stop_collecting:
            self.project = await Project.filter(id=self.project.id).first()
            devices = await Device.filter(project=self.project).all()
            for device in devices:
                if self.stop_collecting:
                    return
                if not device.reading_status:
                    continue
                local_tz = get_timezone()
                now_local = datetime.now(local_tz)
                if device.wait_time > now_local:
                    continue
                main_db_model, tmp_db_model = self.get_db_model(device)
                
                last_report = await main_db_model.filter(device=device).last()
                # new_data = await get_data_from_device(device, self.project, self.main_window)
                
                new_data = get_test_data(device.model, last_report)

                if self.stop_collecting:  # Перевірка
                    return
                if new_data == {}:
                    continue

                tmp_report_data = self.get_tmp_data(device, new_data)

                existing_tmp_report = await tmp_db_model.filter(device_id=device.id).first()
                if existing_tmp_report:
                    for key, value in tmp_report_data.items():
                        setattr(existing_tmp_report, key, value)
                    await existing_tmp_report.save()
                else:
                    tmp_report = tmp_db_model(**tmp_report_data)
                    await tmp_report.save()

                should_record_immediately = False
                for phase in self.phases:
                    if (
                            is_voltage_out_of_range(new_data, device, phase) or
                            is_current_over_limit(new_data, device, phase) or
                            is_power_over_limit(new_data, device, phase)
                    ):
                        should_record_immediately = True
                        break

                if not should_record_immediately:
                    if last_report:
                        device_reading_interval = device.reading_interval
                        last_report_time = last_report.timestamp.replace(tzinfo=None)
                        calculated_time = last_report_time + timedelta(seconds=device_reading_interval)
                        current_time = datetime.now().replace(tzinfo=None)

                        if device.reading_type == 2:
                            reading_time = device.reading_time
                            start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                            if current_time < (
                                    start_of_day + timedelta(
                                minutes=reading_time)) or last_report_time >= start_of_day:
                                continue

                        if calculated_time > current_time:
                            continue

                report_data = {
                    "device_id": device.id,
                }
                report_data.update({key: value for key, value in new_data.items() if value is not None})

                new_report = main_db_model(**report_data)
                await new_report.save()

                if device.actual_status is False:
                    logger.info(f"Device {device.name} - {device.model} - is now online")
                    device.actual_status = True
                    await device.save(force_update=True)

                deleting_time = get_deleting_time()
                if deleting_time > 0:
                    delete_before_date = datetime.now().replace(tzinfo=None) - timedelta(days=deleting_time)
                    first_report = await main_db_model.filter(device=device).first()
                    if first_report and first_report.timestamp.replace(tzinfo=None) < delete_before_date:
                        await first_report.delete()
            if self.stop_collecting:
                return
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
        elif device.model == "SDM72":
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
            self.phases = ['1']
            return SDM120Report, SDM120ReportTmp
        elif device.model == "SDM630":
            self.phases = ['1', '2', '3']
            return SDM630Report, SDM630ReportTmp
        elif device.model == "SDM72":
            self.phases = ['1', '2', '3']
            return SDM72Report, SDM72ReportTmp
        else:
            QMessageBox.warning(
                self.main_window, f"{device.name}", f"{device.model} - Unknown model", QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Cancel)
