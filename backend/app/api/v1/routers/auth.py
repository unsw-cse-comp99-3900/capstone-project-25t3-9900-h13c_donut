# app/api/v1/routers/auth.py
from fastapi import APIRouter, HTTPException, Response, status, Depends
from pydantic import BaseModel
from app.core.security import verify_password, create_access_token, hash_password
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterIn(BaseModel):
    username: str
    email: str | None = None
    password: str

class CheckResetIn(BaseModel):
    username: str
    email: str

class ResetPasswordIn(BaseModel):
    userId: str
    newPassword: str

class ChangePasswordIn(BaseModel):
    newPassword: str

@router.post("/register")
async def register(body: RegisterIn):
    # 基础校验，避免 pydantic 报错变 500
    if not body.username or not body.password:
        return {"success": False, "error": {"code": "BAD_REQUEST", "message": "username/password required"}}
    # 查重
    if await User.get_or_none(username=body.username):
        return {"success": False, "error": {"code": "USERNAME_EXISTS", "message": "Username already exists"}}
    if body.email and await User.get_or_none(email=body.email):
        return {"success": False, "error": {"code": "EMAIL_EXISTS", "message": "Email already registered"}}
    # 创建
    u = await User.create(
        username=body.username,
        email=(body.email or None),
        password_hash=hash_password(body.password),
        role="user",
    )
    return {"success": True, "data": {"id": str(u.id), "username": u.username, "email": u.email}}

@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    user = await User.get_or_none(username=payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"code":"AUTH_INVALID_CREDENTIALS","message":"账号或密码错误"})
    token = create_access_token(str(user.id))
    response.set_cookie("accessToken", token, httponly=True, secure=False, samesite="lax")
    return {"success": True, "data": {"user": {"id": str(user.id), "username": user.username, "email": user.email, "role": user.role},
                                      "accessToken": token}}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": {"id": str(user.id), "username": user.username, "email": user.email, "role": user.role}}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("accessToken")
    return {"success": True}

@router.post("/check-reset")
async def check_reset(body: CheckResetIn):
    u = await User.get_or_none(username=body.username)
    if not u or (u.email or "").lower() != (body.email or "").lower():
        return {"success": False, "error": {"code": "USER_NOT_FOUND", "message": "User not found"}}
    return {"success": True, "data": {"userId": str(u.id)}}

@router.post("/reset-password")
async def reset_password(body: ResetPasswordIn):
    u = await User.get_or_none(id=body.userId)
    if not u:
        return {"success": False, "error": {"code": "USER_NOT_FOUND", "message": "User not found"}}
    u.password_hash = hash_password(body.newPassword)
    await u.save()
    return {"success": True, "data": {"ok": True}}

@router.post("/change-password")
async def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user)):
    user.password_hash = hash_password(body.newPassword)
    await user.save()
    return {"success": True, "data": {"ok": True}}
