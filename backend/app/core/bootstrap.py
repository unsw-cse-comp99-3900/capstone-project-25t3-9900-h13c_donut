# app/core/bootstrap.py
import os
import logging
from app.models.user import User
from app.core.security import hash_password

logger = logging.getLogger("uvicorn.error")

async def ensure_default_admin() -> None:
    """
    若数据库中不存在任何 admin，则基于环境变量创建一个默认 admin。
    仅在以下条件下生效：
      - 目前没有 role="admin" 的用户
      - 且设置了 ADMIN_PASSWORD（避免用默认弱密码）
    环境变量：
      ADMIN_USERNAME (default: "admin")
      ADMIN_EMAIL    (default: "admin@example.com")
      ADMIN_PASSWORD (required, 否则不创建)
    """
    has_admin = await User.filter(role="admin").exists()
    if has_admin:
        return

    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        logger.warning("[bootstrap] No admin present, but ADMIN_PASSWORD not set -> skip creating default admin.")
        return

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")

    # 若用户名已被占用（用户可能用 "admin" 注册了普通账号），创建一个不冲突的名称
    base_username = admin_username
    suffix = 1
    while await User.filter(username=admin_username).exists():
        suffix += 1
        admin_username = f"{base_username}{suffix}"

    u = await User.create(
        username=admin_username,
        email=admin_email,
        password_hash=hash_password(admin_password),
        role="admin",
    )
    logger.warning("[bootstrap] Created default admin -> username=%s email=%s id=%s",
                   u.username, u.email, u.id)
