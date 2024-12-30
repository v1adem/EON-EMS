from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from config import Base


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False, unique=True)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    device_address = Column(Integer, nullable=False)

    reading_type = Column(Integer, nullable=False, default=1)  # 1 for interval, 2 for time
    reading_interval = Column(Integer, nullable=False, default=3600)  # Seconds
    reading_time = Column(Integer, nullable=False, default=0)  # Minutes

    reading_status = Column(Boolean, nullable=False, default=False)  # True = needs reading

    project = relationship("Project")

    def __repr__(self):
        return (f"<Device(id={self.id}, name='{self.name}', manufacturer='{self.manufacturer}', "
                f"model='{self.model}', device_address={self.device_address}, project_id={self.project_id}, "
                f"reading_status={self.reading_status})>")

    def toggle_reading_status(self):
        self.reading_status = not self.reading_status

    def get_reading_status(self):
        return self.reading_status
