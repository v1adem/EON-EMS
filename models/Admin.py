from tortoise import fields
from tortoise.models import Model


class Admin(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255, null=False)
    password = fields.CharField(max_length=255, null=False)
    always_admin = fields.BooleanField(default=False)

    class Meta:
        table = "admin"

    def __str__(self):
        return f"<Admin(username='{self.username}')>"
