from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from tzlocal import get_localzone

from config import Base


class SDM120Report(Base):
    __tablename__ = 'sdm120_reports'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()))

    device = relationship("Device")

    line_voltage_1 = Column(Float, nullable=True)
    current_1 = Column(Float, nullable=True)
    active_power_1 = Column(Float, nullable=True)
    power_1 = Column(Float, nullable=True)
    reactive_power_1 = Column(Float, nullable=True)
    power_factor_1 = Column(Float, nullable=True)
    frequency_1 = Column(Float, nullable=True)
    import_active_energy_1 = Column(Float, nullable=True)
    export_active_energy_1 = Column(Float, nullable=True)
    total_active_energy = Column(Float, nullable=True)
    total_reactive_energy = Column(Float, nullable=True)

    @hybrid_property
    def total_kWh(self):
        return self.total_active_energy + self.total_reactive_energy if self.total_active_energy is not None and self.total_reactive_energy is not None else None

    def __repr__(self):
        return (f"<SDM120Report(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, "
                f"voltage={self.line_voltage_1}, current={self.current_1}, power={self.power_1})>")


class SDM120ReportTmp(Base):
    __tablename__ = 'sdm120_reports_tmp'

    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()), primary_key=True)
    line_voltage_1 = Column(Float, nullable=True)
    current_1 = Column(Float, nullable=True)
    power_1 = Column(Float, nullable=True)
    total_active_energy = Column(Float, nullable=True)
    total_reactive_energy = Column(Float, nullable=True)

    device = relationship("Device")

    @hybrid_property
    def total_kWh(self):
        return self.total_active_energy + self.total_reactive_energy if self.total_active_energy is not None and self.total_reactive_energy is not None else None

    def __repr__(self):
        return (f"<SDM120ReportTmp(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, "
                f"voltage={self.voltage}, current={self.current}, apparent_power={self.apparent_power})>")


class SDM630Report(Base):
    __tablename__ = 'sdm630_reports'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()))

    line_voltage_1 = Column(Float, nullable=True)
    line_voltage_2 = Column(Float, nullable=True)
    line_voltage_3 = Column(Float, nullable=True)
    current_1 = Column(Float, nullable=True)
    current_2 = Column(Float, nullable=True)
    current_3 = Column(Float, nullable=True)
    power_1 = Column(Float, nullable=True)
    power_2 = Column(Float, nullable=True)
    power_3 = Column(Float, nullable=True)
    power_factor_1 = Column(Float, nullable=True)
    power_factor_2 = Column(Float, nullable=True)
    power_factor_3 = Column(Float, nullable=True)
    total_system_power = Column(Float, nullable=True)
    total_system_VA = Column(Float, nullable=True)
    total_system_VAr = Column(Float, nullable=True)
    total_system_power_factor = Column(Float, nullable=True)
    total_import_kwh = Column(Float, nullable=True)
    total_export_kwh = Column(Float, nullable=True)
    total_import_kVAh = Column(Float, nullable=True)
    total_export_kVAh = Column(Float, nullable=True)
    total_kVAh = Column(Float, nullable=True)
    _1_to_2_voltage = Column(Float, nullable=True)
    _2_to_3_voltage = Column(Float, nullable=True)
    _3_to_1_voltage = Column(Float, nullable=True)
    neutral_current = Column(Float, nullable=True)
    line_voltage_THD_1 = Column(Float, nullable=True)
    line_voltage_THD_2 = Column(Float, nullable=True)
    line_voltage_THD_3 = Column(Float, nullable=True)
    line_current_THD_1 = Column(Float, nullable=True)
    line_current_THD_2 = Column(Float, nullable=True)
    line_current_THD_3 = Column(Float, nullable=True)
    current_demand_1 = Column(Float, nullable=True)
    current_demand_2 = Column(Float, nullable=True)
    current_demand_3 = Column(Float, nullable=True)
    phase_voltage_THD_1 = Column(Float, nullable=True)
    phase_voltage_THD_2 = Column(Float, nullable=True)
    phase_voltage_THD_3 = Column(Float, nullable=True)
    average_line_to_line_voltage_THD = Column(Float, nullable=True)
    total_kWh = Column(Float, nullable=True)
    total_kVArh = Column(Float, nullable=True)
    import_kWh_1 = Column(Float, nullable=True)
    import_kWh_2 = Column(Float, nullable=True)
    import_kWh_3 = Column(Float, nullable=True)
    export_kWh_1 = Column(Float, nullable=True)
    export_kWh_2 = Column(Float, nullable=True)
    export_kWh_3 = Column(Float, nullable=True)
    total_kWh_1 = Column(Float, nullable=True)
    total_kWh_2 = Column(Float, nullable=True)
    total_kWh_3 = Column(Float, nullable=True)
    import_kVArh_1 = Column(Float, nullable=True)
    import_kVArh_2 = Column(Float, nullable=True)
    import_kVArh_3 = Column(Float, nullable=True)
    export_kVArh_1 = Column(Float, nullable=True)
    export_kVArh_2 = Column(Float, nullable=True)
    export_kVArh_3 = Column(Float, nullable=True)
    total_kVArh_1 = Column(Float, nullable=True)
    total_kVArh_2 = Column(Float, nullable=True)
    total_kVArh_3 = Column(Float, nullable=True)

    device = relationship("Device")

    def __repr__(self):
        return f"<SDM630Report(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, ...)>"


class SDM630ReportTmp(Base):
    __tablename__ = 'sdm630_reports_tmp'

    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()), primary_key=True)

    line_voltage_1 = Column(Float, nullable=True)
    line_voltage_2 = Column(Float, nullable=True)
    line_voltage_3 = Column(Float, nullable=True)
    current_1 = Column(Float, nullable=True)
    current_2 = Column(Float, nullable=True)
    current_3 = Column(Float, nullable=True)
    power_1 = Column(Float, nullable=True)
    power_2 = Column(Float, nullable=True)
    power_3 = Column(Float, nullable=True)
    total_kWh = Column(Float, nullable=True)

    device = relationship("Device")

    def __repr__(self):
        return f"<SDM630Report(device_id={self.device_id}, timestamp={self.timestamp}, ...)>"
