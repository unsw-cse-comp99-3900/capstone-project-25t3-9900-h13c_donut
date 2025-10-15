# app/core/security.py
import os
import datetime as dt
import jwt  # PyJWT
from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# 只用 argon2，完全绕过 bcrypt（开发期最省心）
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_ALG = "HS256"

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    now = dt.datetime.utcnow()
    payload = {"sub": user_id, "iat": now, "exp": now + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
