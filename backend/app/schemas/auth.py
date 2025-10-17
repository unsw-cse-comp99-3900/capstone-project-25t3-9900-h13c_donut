# app/schemas/auth.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    role: str = "user"

class LoginResponse(BaseModel):
    user: UserOut
    accessToken: str
