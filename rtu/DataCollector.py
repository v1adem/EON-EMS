import asyncio
import logging
from datetime import datetime, timedelta

import pytz

from models.Project import Project
from rtu.DataCollectorTestingTools import get_test_data

logger = logging.getLogger(__name__)

from AsyncioPySide6 import AsyncioPySide6
from PySide6.QtCore import QRunnable

from tools.config import get_deleting_time, get_timezone
from models.Device import Device
from models.Report import SDM120Report, SDM120ReportTmp, SDM630Report, SDM72Report, SDM630ReportTmp, SDM72ReportTmp


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
        self.main_window = main_window
        self.stop_collecting = False

    def run(self):
        AsyncioPySide6.runTask(self.collect_data())

    async def collect_data(self):
        while not self.stop_collecting:
            try:
                self.project = await Project.filter(id=self.project.id).first()
                devices = await Device.filter(project=self.project).all()
                for device in devices:
                    await self.handle_device_reading(device)
            except Exception as e:
                logger.error(f"Error in main collection loop: {e}")

            if not self.stop_collecting:
                await asyncio.sleep(1)

    async def handle_device_reading(self, device):
        try:
            local_tz = get_timezone()
            now_local = datetime.now(local_tz)
            if device.reading_status is False:
                return
            if device.wait_time and device.wait_time > now_local:
                return

            last_report = await self.get_last_report(device)
            new_data = get_test_data(device.model, last_report)

            if not new_data or new_data == {}:
                await self.handle_read_error(device)
                return

            await self.handle_successful_reading(device, new_data)

        except Exception as e:
            logger.error(f"Unexpected error handling device {device.name}: {e}")
            await self.update_device_status(device, False)

    async def update_device_status(self, device, is_online):
        try:
            if device.actual_status != is_online:
                device.actual_status = is_online

                if not is_online:
                    tz = get_timezone()
                    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                    wait_time_local = now_utc + timedelta(seconds=300)
                    device.wait_time = wait_time_local.astimezone(tz)

                await device.save(update_fields=['actual_status', 'wait_time'])

                if self.main_window.project_view_widget is not None:
                    self.main_window.project_view_widget.load_devices()

                status_msg = "online" if is_online else "offline"
                logger.info(f"Device {device.name} - {device.model} is now {status_msg}")
        except Exception as e:
            logger.error(f"Error updating device {device.name} status: {e}")

    async def handle_read_error(self, device):
        await self.update_device_status(device, False)

    async def handle_successful_reading(self, device, new_data):
        if not device.actual_status:
            await self.update_device_status(device, True)

        phases = get_phases(device)
        immediate_record = any(
            is_voltage_out_of_range(new_data, device, phase) or
            is_current_over_limit(new_data, device, phase) or
            is_power_over_limit(new_data, device, phase)
            for phase in phases
        )

        if not immediate_record:
            last_report = await self.get_last_report(device)
            if last_report and not self.should_record_now(device, last_report):
                return

        await self.save_device_data(device, new_data)

    async def get_last_report(self, device):
        main_db_model, _ = self.get_db_model(device)
        return await main_db_model.filter(device=device).last()

    def should_record_now(self, device, last_report):
        device_reading_interval = device.reading_interval
        last_report_time = last_report.timestamp.replace(tzinfo=None)
        calculated_time = last_report_time + timedelta(seconds=device_reading_interval)
        current_time = datetime.now().replace(tzinfo=None)

        if device.reading_type == 2:
            reading_time = device.reading_time
            start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return current_time >= (start_of_day + timedelta(minutes=reading_time)) and last_report_time < start_of_day

        return current_time >= calculated_time

    async def save_device_data(self, device, new_data):
        try:
            main_db_model, tmp_db_model = self.get_db_model(device)

            tmp_report_data = get_tmp_data(device, new_data)
            existing_tmp_report = await tmp_db_model.filter(device_id=device.id).first()

            if existing_tmp_report:
                for key, value in tmp_report_data.items():
                    setattr(existing_tmp_report, key, value)
                await existing_tmp_report.save()
            else:
                tmp_report = tmp_db_model(**tmp_report_data)
                await tmp_report.save()

            report_data = {"device_id": device.id}
            report_data.update({key: value for key, value in new_data.items() if value is not None})

            new_report = main_db_model(**report_data)
            await new_report.save()

            logger.info(f"Report saved - {device.name}, {device.model}")

            await self.clean_old_records(device, main_db_model)

        except Exception as e:
            logger.error(f"Error saving data for device {device.name}: {e}")

    async def clean_old_records(self, device, db_model):
        deleting_time = get_deleting_time()
        if deleting_time > 0:
            delete_before_date = datetime.now().replace(tzinfo=None) - timedelta(days=deleting_time)
            first_report = await db_model.filter(device=device).first()
            if first_report and first_report.timestamp.replace(tzinfo=None) < delete_before_date:
                await first_report.delete()

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
            logger.error("Unknown device model")

def get_tmp_data(device, new_data):
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
        return {}


def get_phases(device):
    if device.model == "SDM120":
        return ['1']
    elif device.model == "SDM630":
        return ['1', '2', '3']
    elif device.model == "SDM72":
        return ['1', '2', '3']
    else:
        logger.error("Unknown device model")

