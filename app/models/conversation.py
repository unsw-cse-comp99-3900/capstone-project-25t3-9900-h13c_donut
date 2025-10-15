# app/models/conversation.py
import uuid
from tortoise import fields, models

class Conversation(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="conversations", on_delete=fields.CASCADE)
    title = fields.CharField(max_length=128, null=True)
    accent = fields.CharField(max_length=8)           # Sprint1: 'us'
    model = fields.CharField(max_length=16, default="free")
    started_at = fields.DatetimeField(auto_now_add=True)
    ended_at = fields.DatetimeField(null=True)
    duration_sec = fields.IntField(null=True)

    class Meta:
        table = "conversations"
