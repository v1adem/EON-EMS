from tortoise import fields
from tortoise.models import Model


class Device(Model):
    id = fields.IntField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="devices", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, unique=True)
    manufacturer = fields.CharField(max_length=255)
    model = fields.CharField(max_length=255)
    device_address = fields.IntField()

    reading_type = fields.IntField(default=1)  # 1 for interval, 2 for time
    reading_interval = fields.IntField(default=3600)  # Seconds
    reading_time = fields.IntField(default=0)  # Minutes

    reading_status = fields.BooleanField(default=False)  # True = needs reading

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
