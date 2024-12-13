from pymodbus.client import ModbusSerialClient
from sqlalchemy import Column, Integer, String
from config import Base


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    baudrate = Column(Integer, nullable=False, default=9600)
    bytesize = Column(Integer, nullable=False, default=8)
    stopbits = Column(Integer, nullable=False, default=1)
    parity = Column(String, nullable=False, default='N')  # 'N', 'E', 'O', etc.

    is_connected = False

    def __repr__(self):
        return (f"<Project(id={self.id}, name='{self.name}', description='{self.description}', "
                f"port={self.port}, baudrate={self.baudrate}, bytesize={self.bytesize}, "
                f"stopbits={self.stopbits}, parity='{self.parity}')>")
