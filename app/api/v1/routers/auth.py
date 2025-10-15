# app/api/v1/routers/auth.py
from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.auth import LoginRequest
from app.core.security import verify_password, create_access_token, hash_password
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    user = await User.get_or_none(username=payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"code":"AUTH_INVALID_CREDENTIALS","message":"账号或密码错误"})
    token = create_access_token(str(user.id))
    # 下发 HttpOnly Cookie（前端也能用 response body 的 accessToken）
    response.set_cookie("accessToken", token, httponly=True, secure=False, samesite="lax")
    return {"success": True, "data": {"user": {"id": str(user.id), "username": user.username, "role": user.role},
                                      "accessToken": token}}

# --- 开发期便利：种子用户（只用于本地，确认后可删除/注释） ---
@router.post("/seed-user")
async def seed_user():
    exists = await User.get_or_none(username="alice@example.com")
    if exists:
        return {"created": False, "user": {"id": str(exists.id), "username": exists.username}}
    u = await User.create(
        username="alice@example.com",
        password_hash=hash_password("Str0ngP@ss!"),
        role="user",
    )
    return {"created": True, "user": {"id": str(u.id), "username": u.username}}

from pydantic import BaseModel

class DevCreateUserIn(BaseModel):
    username: str
    password: str
    role: str = "user"

