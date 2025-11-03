# app/api/v1/routers/admin.py
from __future__ import annotations

import datetime as dt
import secrets
import string
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel
from tortoise.expressions import Q

from app.api.v1.deps import require_admin, get_current_user
from app.models.user import User
from app.models.license_key import LicenseKey
from app.schemas.admin import (
    AdminUserListOut,
    AdminUserDetailOut,
    AdminUserUpdateIn,
    AdminResetPasswordIn,
)
from app.schemas.license_key import (
    BatchGenerateIn,
    BatchGenerateOut,
    GeneratedKeyItem,
    VerifyKeyIn,
)
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ------------------------------------------------------------------------------
# 辅助：可选的当前用户（用于 /admin/verify-key 在 consume=True 时记录兑换者）
# ------------------------------------------------------------------------------
async def optional_current_user_dependency():
    """
    尝试获取当前登录用户；失败则返回 None（而不是抛 401）。
    用于 /admin/verify-key 在 consume=True 时记录 used_by。
    """
    try:
        user = await get_current_user()  # 会尝试从 Authorization/Cookie 取 token
        return user
    except Exception:
        return None


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# ==============================================================================
# 一、用户管理接口
#     前缀：/api/v1/admin/users
# ==============================================================================
def _user_to_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


async def _count_admins() -> int:
    return await User.filter(role="admin").count()


@router.get(
    "/users",
    response_model=AdminUserListOut,
    dependencies=[Depends(require_admin)],
)
async def list_users(
    q: str | None = Query(default=None, description="按 username/email 模糊搜索"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    qs = User.all().order_by("-created_at")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

    total = await qs.count()
    rows = await qs.offset(offset).limit(limit)
    items = [_user_to_dict(u) for u in rows]

    return {"items": items, "offset": offset, "limit": limit, "total": total}


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailOut,
    dependencies=[Depends(require_admin)],
)
async def get_user_detail(user_id: str):
    u = await User.get_or_none(id=user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")
    return {"user": _user_to_dict(u)}


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserDetailOut,
    dependencies=[Depends(require_admin)],
)
async def update_user(
    user_id: str,
    body: AdminUserUpdateIn,
    current_admin: User = Depends(get_current_user),
):
    u = await User.get_or_none(id=user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")

    # 1) 用户名更新（唯一性检查）
    if body.username and body.username != u.username:
        exists = await User.filter(username=body.username).exclude(id=user_id).exists()
        if exists:
            raise HTTPException(
                status_code=400,
                detail={"code": "USERNAME_EXISTS", "message": "Username already exists"},
            )
        u.username = body.username

    # 2) 邮箱更新（唯一性检查，允许 null）
    if body.email is not None and body.email != u.email:
        if body.email != "":
            email_taken = await User.filter(email=body.email).exclude(id=user_id).exists()
            if email_taken:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "EMAIL_EXISTS", "message": "Email already registered"},
                )
            u.email = body.email
        else:
            u.email = None

    # 3) 角色更新（不能把自己降级；不能把最后一个 admin 降为 user）
    if body.role and body.role != u.role:
        if str(current_admin.id) == str(u.id) and body.role != "admin":
            raise HTTPException(
                status_code=400,
                detail={"code": "CANNOT_DEMOTE_SELF", "message": "Cannot demote yourself"},
            )

        if u.role == "admin" and body.role == "user":
            admin_count = await _count_admins()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail={"code": "LAST_ADMIN_FORBIDDEN", "message": "Cannot demote the last admin"},
                )
        u.role = body.role

    await u.save()
    return {"user": _user_to_dict(u)}


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: str,
    current_admin: User = Depends(get_current_user),
):
    u = await User.get_or_none(id=user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")

    # 不能删除自己
    if str(current_admin.id) == str(u.id):
        raise HTTPException(
            status_code=400,
            detail={"code": "CANNOT_DELETE_SELF", "message": "Cannot delete yourself"},
        )

    # 不能删除最后一个 admin
    if u.role == "admin":
        admin_count = await _count_admins()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail={"code": "LAST_ADMIN_FORBIDDEN", "message": "Cannot delete the last admin"},
            )

    await u.delete()
    return {"success": True, "data": {"ok": True}}


@router.post(
    "/users/{user_id}/reset-password",
    dependencies=[Depends(require_admin)],
)
async def reset_user_password(
    user_id: str,
    body: AdminResetPasswordIn,
    current_admin: User = Depends(get_current_user),
):
    u = await User.get_or_none(id=user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USER_NOT_FOUND")

    u.password_hash = hash_password(body.newPassword)
    await u.save()
    return {"success": True, "data": {"ok": True}}


# ==============================================================================
# 二、密钥管理（批量生成、列表、详情、删除）
#     前缀：/api/v1/admin/license-keys/*
#     说明：不返回明文，只在生成时返回一次明文集合
# ==============================================================================
def _make_plain_key(prefix: str = "FAT") -> str:
    """
    生成形如 FAT-AB12-CD34-EF56-GH78 的密钥明文。
    仅返回给前端一次；库中只保存 sha256(key)。
    """
    alphabet = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(alphabet) for _ in range(4)) for __ in range(4)]
    return f"{prefix}-{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"


@router.post(
    "/license-keys/batch",
    response_model=BatchGenerateOut,
    dependencies=[Depends(require_admin)],
)
async def batch_generate_keys(body: BatchGenerateIn):
    """
    批量生成密钥：
    - 入库只存 hash，不存明文
    - 返回给前端一次性明文列表（用于导出/发放）
    """
    count = body.count
    key_type = body.keyType.strip()
    prefix = (body.prefix or "FAT").strip().upper()
    expires_at: Optional[dt.datetime] = None

    if body.expireDays:
        expires_at = utc_now() + dt.timedelta(days=body.expireDays)

    items: List[GeneratedKeyItem] = []

    for _ in range(count):
        # 确保 hash 唯一
        for __ in range(10):  # 最多尝试 10 次避免极端重复
            plain = _make_plain_key(prefix)
            h = LicenseKey.sha256_hex(plain)
            exists = await LicenseKey.filter(key_hash=h).exists()
            if not exists:
                lk = await LicenseKey.create(
                    key_hash=h,
                    key_type=key_type,
                    expires_at=expires_at,
                    is_used=False,
                )
                items.append(
                    GeneratedKeyItem(
                        id=str(lk.id),
                        key=plain,  # 只在生成接口返回明文
                        keyType=key_type,
                        expiresAt=lk.expires_at.isoformat() if lk.expires_at else None,
                    )
                )
                break
        else:
            # 连续 10 次碰撞，极小概率；报错提示
            raise HTTPException(status_code=500, detail="KEY_GENERATION_COLLISION")

    return {"keys": items}


class LicenseKeyListOut(BaseModel):
    items: list[dict]
    offset: int
    limit: int
    total: int


@router.get(
    "/license-keys",
    response_model=LicenseKeyListOut,
    dependencies=[Depends(require_admin)],
)
async def list_license_keys(
    is_used: Optional[bool] = Query(default=None),
    key_type: Optional[str] = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
):
    qs = LicenseKey.all().order_by("-created_at")
    if is_used is not None:
        qs = qs.filter(is_used=is_used)
    if key_type:
        qs = qs.filter(key_type=key_type)

    total = await qs.count()
    rows = await qs.offset(offset).limit(limit)

    now = utc_now()
    items = []
    for r in rows:
        expired = bool(r.expires_at and r.expires_at <= now)
        items.append(
            {
                "id": str(r.id),
                "keyType": r.key_type,
                "isUsed": r.is_used,
                "usedBy": str(r.used_by_id) if r.used_by_id else None,
                "usedAt": r.used_at.isoformat() if r.used_at else None,
                "expiresAt": r.expires_at.isoformat() if r.expires_at else None,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "isExpired": expired,
            }
        )

    return {"items": items, "offset": offset, "limit": limit, "total": total}


@router.get(
    "/license-keys/{key_id}",
    dependencies=[Depends(require_admin)],
)
async def get_license_key_detail(key_id: str):
    r = await LicenseKey.get_or_none(id=key_id)
    if not r:
        raise HTTPException(status_code=404, detail="KEY_NOT_FOUND")
    now = utc_now()
    return {
        "success": True,
        "data": {
            "id": str(r.id),
            "keyType": r.key_type,
            "isUsed": r.is_used,
            "usedBy": str(r.used_by_id) if r.used_by_id else None,
            "usedAt": r.used_at.isoformat() if r.used_at else None,
            "expiresAt": r.expires_at.isoformat() if r.expires_at else None,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "isExpired": bool(r.expires_at and r.expires_at <= now),
        },
    }


@router.delete(
    "/license-keys/{key_id}",
    dependencies=[Depends(require_admin)],
)
async def delete_license_key(key_id: str):
    r = await LicenseKey.get_or_none(id=key_id)
    if not r:
        raise HTTPException(status_code=404, detail="KEY_NOT_FOUND")
    await r.delete()
    return {"success": True, "data": {"ok": True}}


# ==============================================================================
# 三、密钥校验（兼容前端：/api/v1/admin/verify-key）
#     说明：
#       - 出于兼容性，这里不强制管理员；普通用户也可调用校验/兑换
#       - body.consume=True 时，如已登录，将记录 used_by；否则只标记使用
# ==============================================================================
@router.post("/verify-key")
async def verify_key(
    body: VerifyKeyIn,
    current_user: Optional[User] = Depends(optional_current_user_dependency),
):
    plain = (body.key or "").strip().upper()
    if not plain:
        return {"success": False, "error": {"code": "BAD_REQUEST", "message": "key required"}}

    h = LicenseKey.sha256_hex(plain)
    r = await LicenseKey.get_or_none(key_hash=h)
    if not r:
        return {"success": True, "data": {"ok": False}}  # 不暴露更多信息

    # 过期判断
    if r.expires_at and r.expires_at <= utc_now():
        return {"success": True, "data": {"ok": False}}

    # 已用判断
    if r.is_used:
        return {"success": True, "data": {"ok": False}}

    # 仅校验：返回 ok=True
    if not body.consume:
        return {"success": True, "data": {"ok": True}}

    # consume=True：标记使用；如有登录用户则记录 used_by
    r.is_used = True
    r.used_at = utc_now()
    if current_user:
        r.used_by = current_user
    await r.save()
    return {"success": True, "data": {"ok": True}}
