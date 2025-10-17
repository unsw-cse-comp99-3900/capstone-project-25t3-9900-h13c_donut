import uuid
from tortoise import fields, models

class User(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    username = fields.CharField(max_length=256, unique=True, index=True)
    email = fields.CharField(max_length=256, null=True)  # 新增
    password_hash = fields.CharField(max_length=255)
    role = fields.CharField(max_length=16, default="user")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"
