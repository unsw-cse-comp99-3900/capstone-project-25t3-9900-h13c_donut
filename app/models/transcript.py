# app/models/transcript.py
from tortoise import fields, models

class Transcript(models.Model):
    id = fields.IntField(pk=True)
    conversation = fields.ForeignKeyField("models.Conversation", related_name="transcripts", on_delete=fields.CASCADE)
    seq = fields.IntField()               # 1..N
    is_final = fields.BooleanField(default=True)
    start_ms = fields.IntField(null=True)
    end_ms = fields.IntField(null=True)
    text = fields.TextField()

    class Meta:
        table = "transcripts"
        ordering = ["seq"]
