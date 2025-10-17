# app/models/transcript.py
import uuid
from tortoise import fields, models

class Transcript(models.Model):
    id = fields.IntField(pk=True)  # 或者 UUID，看你当前定义
    conversation = fields.ForeignKeyField("models.Conversation", related_name="transcripts")

    seq = fields.IntField()              # 段序号，int4 足够
    is_final = fields.BooleanField()

    # ↓↓↓ 把 IntField 改成 BigIntField（支持毫秒级时间戳）
    start_ms = fields.BigIntField(null=True)
    end_ms   = fields.BigIntField(null=True)

    text = fields.TextField()
    audio_url = fields.CharField(max_length=1024, null=True)
