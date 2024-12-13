from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from datetime import datetime
from tzlocal import get_localzone

from config import Base


class SDM120Report(Base):
    __tablename__ = 'sdm120_reports'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()))

    device = relationship("Device")

    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    active_power = Column(Float, nullable=True)
    apparent_power = Column(Float, nullable=True)
    reactive_power = Column(Float, nullable=True)
    frequency = Column(Float, nullable=True)
    import_active_energy = Column(Float, nullable=True)
    export_active_energy = Column(Float, nullable=True)
    total_active_energy = Column(Float, nullable=True)
    total_reactive_energy = Column(Float, nullable=True)

    def __repr__(self):
        return (f"<SDM120Report(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, "
                f"voltage={self.voltage}, current={self.current}, active_power={self.active_power})>")


class SDM120ReportTmp(Base):
    __tablename__ = 'sdm120_reports_tmp'

    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(get_localzone()), primary_key=True)
    voltage = Column(Float, nullable=True)
    current = Column(Float, nullable=True)
    active_power = Column(Float, nullable=True)
    total_active_energy = Column(Float, nullable=True)

    device = relationship("Device")

    def __repr__(self):
        return (f"<SDM120ReportTmp(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, "
                f"voltage={self.voltage}, current={self.current}, apparent_power={self.apparent_power})>")


class SDM630Report(Base):
    __tablename__ = 'sdm630_reports'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    device = relationship("Device")

    additional_param = Column(Float, nullable=True)

    def __repr__(self):
        return (f"<SDM630Report(id={self.id}, device_id={self.device_id}, timestamp={self.timestamp}, "
                f"voltage={self.voltage}, current={self.current}, additional_param_2={self.additional_param_2})>")
