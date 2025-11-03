# app/models/license_key.py
import uuid
import hashlib
from typing import Optional
from tortoise import fields, models

class LicenseKey(models.Model):
    """
    购买 / 升级的兑换密钥。只存 hash，不存明文。
    - key_hash: sha256(明文key) 的 64位十六进制字符串，唯一
    - expires_at: 过期时间（可选）
    - is_used: 是否已被兑换
    - used_by: 兑换者（User外键，可为空）
    - used_at: 兑换时间
    - created_at: 创建时间
    """
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    key_hash = fields.CharField(max_length=64, unique=True, index=True)
    key_type = fields.CharField(max_length=16, default="paid")  # 预留类型：paid / trial / etc
    expires_at = fields.DatetimeField(null=True)
    is_used = fields.BooleanField(default=False)

    used_by: Optional[fields.ForeignKeyNullableRelation["User"]] = fields.ForeignKeyField(
        "models.User", related_name="license_keys", null=True
    )
    used_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "license_keys"

    @staticmethod
    def sha256_hex(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
