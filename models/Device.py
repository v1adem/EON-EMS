from datetime import datetime

import pytz
from tortoise import fields
from tortoise.models import Model

from tools.config import get_timezone


def default_wait_time():
    tz = get_timezone()
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    return now_utc.astimezone(tz)

class Device(Model):
    id = fields.IntField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="devices", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, unique=True)
    manufacturer = fields.CharField(max_length=255)
    model = fields.CharField(max_length=255)
    device_address = fields.IntField()

    minV = fields.IntField(default=100)
    maxV = fields.IntField(default=500)
    maxA = fields.IntField(default=100)
    maxW = fields.IntField(default=99999)

    reading_type = fields.IntField(default=1)  # 1 for interval, 2 for time
    reading_interval = fields.IntField(default=1800)  # Seconds
    reading_time = fields.IntField(default=30)  # Minutes

    reading_status = fields.BooleanField(default=False)  # True = needs reading
    actual_status = fields.BooleanField(default=False)  # True = connected
    wait_time = fields.DatetimeField(default=default_wait_time)

    class Meta:
        table = "devices"

    def __str__(self):
        return (f"<Device(id={self.id}, name='{self.name}', manufacturer='{self.manufacturer}', "
                f"model='{self.model}', device_address={self.device_address}, project_id={self.project_id}, "
                f"reading_status={self.reading_status})>")

    def toggle_reading_status(self):
        self.reading_status = not self.reading_status

    def get_reading_status(self):
        return self.reading_status
