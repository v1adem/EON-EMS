from datetime import datetime, timedelta
from time import sleep

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from models.Device import Device
from models.Project import Project
from models.Report import SDM120Report, SDM630Report, SDM120ReportTmp
from rtu.SerialReaderRS485 import SerialReaderRS485


def get_data_from_device(device, project, properties_list, main_window):
    try:
        print(f"{device.name} - Reading started")
        client = SerialReaderRS485(device.name, device.model, project.port, device.device_address, project.baudrate,
                                   project.bytesize, project.parity, project.stopbits, main_window)
        return client.read_all_properties(properties_list)
    except Exception as e:
        QMessageBox.warning(main_window, title="Помилка зчитування", text=f"{device.name} - {e}")


class SDM630ReportTmp:
    pass


class DataCollector(QObject):
    def __init__(self, db_session, project, main_window):
        super().__init__()
        self.main_window = main_window
        self.db_session = db_session
        self.project = project

    def collect_data(self):
        devices = (
            self.db_session.query(Device)
            .filter(Device.project_id == self.project.id)
            .all()
        )
        for device in devices:
            if device.reading_status is False:
                continue

            if device.model == "SDM120":
                self.collect_data_sdm120(device)
            elif device.model == "SDM630":
                self.collect_data_sdm630(device)
            else:
                QMessageBox.warning(parent=self.main_window, title=f"{device.name}", text=f"{device.model} - Невідома модель")
                continue

    def collect_data_sdm120(self, device):
        last_report = (
            self.db_session.query(SDM120Report)
            .filter(SDM120Report.device_id == device.id)
            .order_by(SDM120Report.timestamp.desc())
            .first()
        )

        properties_list = device.get_parameter_names()
        project = self.db_session.query(Project).filter(Project.id == self.project.id).first()
        new_data = get_data_from_device(device, project, properties_list, self.main_window)

        if all(value is None for value in new_data.values()):
            return

        tmp_report_data = {
            "device_id": device.id,
            "voltage": new_data.get("voltage"),
            "current": new_data.get("current"),
            "active_power": new_data.get("active_power"),
            "total_active_energy": new_data.get("total_active_energy"),
        }

        tmp_report = SDM120ReportTmp(**tmp_report_data)
        self.db_session.add(tmp_report)
        self.db_session.commit()

        tmp_reports = (
            self.db_session.query(SDM120ReportTmp)
            .filter(SDM120ReportTmp.device_id == device.id)
            .order_by(SDM120ReportTmp.timestamp.desc())
            .all()
        )
        if len(tmp_reports) > 10:
            oldest_report = tmp_reports[-1]
            self.db_session.delete(oldest_report)
            self.db_session.commit()

        if last_report:
            device_reading_interval = device.reading_interval - 10
            if device.reading_type == 2:
                reading_time = last_report.reading_time
                start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if datetime.now() < (
                        start_of_day + timedelta(minutes=reading_time)) or last_report.timestamp >= start_of_day:
                    return

            if last_report.timestamp + timedelta(seconds=device_reading_interval) > datetime.now():
                return

        report_data = {
            "device_id": device.id,
        }
        report_data.update({key: value for key, value in new_data.items() if value is not None})

        new_report = SDM120Report(**report_data)
        self.db_session.add(new_report)
        self.db_session.commit()

    def collect_data_sdm630(self, device):
        last_report = (
            self.db_session.query(SDM630Report)
            .filter(SDM630Report.device_id == device.id)
            .order_by(SDM630Report.timestamp.desc())
            .first()
        )

        properties_list = device.get_parameter_names()
        project = self.db_session.query(Project).filter(Project.id == self.project.id).first()
        new_data = get_data_from_device(device, project, properties_list, self.main_window)

        if all(value is None for value in new_data.values()):
            return

        tmp_report_data = {
            "device_id": device.id,
            "voltage": new_data.get("voltage"),
            "current": new_data.get("current"),
            "active_power": new_data.get("active_power"),
            "total_active_energy": new_data.get("total_active_energy"),
        }

        tmp_report = SDM630ReportTmp(**tmp_report_data)
        self.db_session.add(tmp_report)
        self.db_session.commit()

        tmp_reports = (
            self.db_session.query(SDM630ReportTmp)
            .filter(SDM630ReportTmp.device_id == device.id)
            .order_by(SDM630ReportTmp.timestamp.desc())
            .all()
        )
        if len(tmp_reports) > 10:
            oldest_report = tmp_reports[-1]
            self.db_session.delete(oldest_report)
            self.db_session.commit()

        if last_report:
            device_reading_interval = device.reading_interval - 10
            if device.reading_type == 2:
                reading_time = last_report.reading_time
                start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if datetime.now() < (
                        start_of_day + timedelta(minutes=reading_time)) or last_report.timestamp >= start_of_day:
                    return

            if last_report.timestamp + timedelta(seconds=device_reading_interval) > datetime.now():
                return

        report_data = {
            "device_id": device.id,
        }
        report_data.update({key: value for key, value in new_data.items() if value is not None})

        new_report = SDM630Report(**report_data)
        self.db_session.add(new_report)
        self.db_session.commit()