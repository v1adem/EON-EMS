from tortoise import fields
from tortoise.models import Model


class Project(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)
    port = fields.IntField(null=True)
    baudrate = fields.IntField(default=9600)
    bytesize = fields.IntField(default=8)
    stopbits = fields.IntField(default=1)
    parity = fields.CharField(max_length=1, default='N')  # 'N', 'E', 'O', etc.

    is_connected: bool = False

    class Meta:
        table = "projects"

    def __str__(self):
        return (f"<Project(id={self.id}, name='{self.name}', description='{self.description}', "
                f"port={self.port}, baudrate={self.baudrate}, bytesize={self.bytesize}, "
                f"stopbits={self.stopbits}, parity='{self.parity}')>")