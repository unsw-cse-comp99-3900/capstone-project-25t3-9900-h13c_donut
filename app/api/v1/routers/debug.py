from fastapi import APIRouter
from app.models.user import User
from app.core.db import init_db

router = APIRouter(prefix="/debug", tags=["debug"])

@router.post("/seed-user")
async def seed_user():
    # 仅开发测试使用：创建一个用户（密码后续用 hash）
    u = await User.create(username="alice@example.com", password_hash="__to_be_set__", role="user")
    return {"id": str(u.id), "username": u.username}
