import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from tortoise.transactions import in_transaction

from models.Project import Project
from models.Device import Device
from models.Report import SDM120Report, SDM630Report, SDM72Report
from rtu.SerialReaderRS485 import SerialReaderRS485
from tools.config import get_deleting_time, get_timezone, get_warnings
from tools.ThreadManager import data_bridge

logger = logging.getLogger(__name__)


def is_voltage_out_of_range(new_data, device, phase):
    voltage_key = f"line_voltage_{phase}"
    voltage_value = new_data.get(voltage_key)
    if voltage_value is not None:
        if voltage_value > device.maxV:
            logger.warning(
                f"Voltage of {phase} phase in {device.name} ({device.model}) is above ({device.maxV}V). Current: {voltage_value}V.")
            return True
        elif voltage_value < device.minV:
            if voltage_value == 0:
                return False
            logger.warning(
                f"Voltage of {phase} phase in {device.name} ({device.model}) is less than ({device.minV}V). Current: {voltage_value}V.")
            return True
    return False


def is_current_over_limit(new_data, device, phase):
    current_key = f"current_{phase}"
    current_value = new_data.get(current_key)
    if current_value is not None and current_value > device.maxA:
        logger.warning(
            f"Current of {phase} phase in {device.name} ({device.model}) is above ({device.maxA}A). Current: {current_value}A.")
        return True
    return False


def is_power_over_limit(new_data, device, phase):
    power_key = f"power_{phase}"
    power_value = new_data.get(power_key)
    if power_value is not None and power_value > device.maxW:
        logger.warning(
            f"Power of {phase} phase in {device.name} ({device.model}) is above ({device.maxW}W). Current: {power_value}W.")
        return True
    return False


def get_phases(model):
    return ['1'] if model == "SDM120" else ['1', '2', '3']


def get_db_model(model):
    if model == "SDM120":
        return SDM120Report
    elif model == "SDM630":
        return SDM630Report
    elif model == "SDM72":
        return SDM72Report
    return None


async def should_record_now(device, last_report):
    if not last_report:
        return True

    # Використовуємоutcnow() для синхронізації з форматом збереження
    current_time_utc = datetime.utcnow()
    last_report_time_utc = last_report.timestamp.astimezone(pytz.utc).replace(tzinfo=None)

    if device.reading_type == 2:  # За часом доби
        # Для порівняння часу доби переводимо UTC в локальний час конфігу
        local_tz = get_timezone()
        current_local = datetime.now(local_tz)
        last_report_local = last_report.timestamp.astimezone(local_tz)

        start_of_day_local = current_local.replace(hour=0, minute=0, second=0, microsecond=0)
        target_time_local = start_of_day_local + timedelta(minutes=device.reading_time)

        return current_local >= target_time_local and last_report_local < start_of_day_local

    # За інтервалом (чисте порівняння в UTC без зсувів часових поясів)
    return current_time_utc >= (last_report_time_utc + timedelta(seconds=device.reading_interval))


async def clean_old_records(device, db_model):
    deleting_time = get_deleting_time()
    if deleting_time > 0:
        delete_before_date = datetime.now(pytz.utc) - timedelta(days=deleting_time)
        await db_model.filter(device=device, timestamp__lt=delete_before_date).delete()


async def handle_device_reading(device, project):
    if not device.reading_status:
        return

    local_tz = get_timezone()
    now_local = datetime.now(local_tz)
    if device.wait_time and device.wait_time > now_local:
        return

    reader = SerialReaderRS485(device, project)
    new_data = await reader.read_all_properties()

    if not new_data:
        if device.actual_status:
            device.actual_status = False
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            device.wait_time = (now_utc + timedelta(seconds=300)).astimezone(local_tz)
            await device.save(update_fields=['actual_status', 'wait_time'])

            wait_str = device.wait_time.strftime('%H:%M')
            data_bridge.device_status_changed.emit(device.id, False, wait_str)
        return

    if not device.actual_status:
        device.actual_status = True
        device.wait_time = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(local_tz)
        await device.save(update_fields=['actual_status', 'wait_time'])
        data_bridge.device_status_changed.emit(device.id, True, "")

    data_bridge.device_data_received.emit(project.id, device.id, new_data)

    immediate_record = False
    if get_warnings():
        phases = get_phases(device.model)
        immediate_record = any(
            is_voltage_out_of_range(new_data, device, phase) or
            is_current_over_limit(new_data, device, phase) or
            is_power_over_limit(new_data, device, phase)
            for phase in phases
        )

    db_model = get_db_model(device.model)
    if not db_model:
        return

    last_report = await db_model.filter(device=device).order_by("-timestamp").first()
    if immediate_record or await should_record_now(device, last_report):
        try:
            report_data = {"device_id": device.id, "timestamp": datetime.now(pytz.utc)}
            report_data.update({key: value for key, value in new_data.items() if value is not None})

            async with in_transaction():
                new_report = db_model(**report_data)
                await new_report.save()
                await clean_old_records(device, db_model)

            logger.info(f"Scheduled report saved for {device.name} ({device.model})")
        except Exception as e:
            logger.error(f"Error saving report for device {device.name}: {e}")


async def collect_data_for_project(project):
    logger.info(f"Starting async collector loop for project line: {project.name}")
    try:
        while True:
            active_project = await Project.filter(id=project.id).first()
            if not active_project:
                break

            devices = await Device.filter(project=active_project).all()

            for device in devices:
                await handle_device_reading(device, active_project)
                await asyncio.sleep(0.05)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info(f"Collector loop for project {project.name} was stopped.")
    except Exception as e:
        logger.error(f"Critical error in collector loop {project.name}: {e}")