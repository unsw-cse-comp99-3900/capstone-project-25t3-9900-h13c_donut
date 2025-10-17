# app/api/v1/deps.py
from fastapi import Depends, Header, HTTPException, Request, status
from app.core.security import decode_access_token
from app.models.user import User

async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
):
    token = None
    # 1) 优先 Authorization: Bearer xxx
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    # 2) 其次 HttpOnly Cookie: accessToken
    if not token:
        token = request.cookies.get("accessToken")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_REQUIRED")

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_INVALID_TOKEN")

    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_USER_NOT_FOUND")
    return user
