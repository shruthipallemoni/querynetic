"""
Password hashing and JWT creation/verification.

Rule this file enforces: a plain-text password is NEVER stored or compared
directly, anywhere. Only its hash ever touches the database.

Uses the `bcrypt` library directly rather than through `passlib` — passlib
is unmaintained and has a known incompatibility with recent bcrypt
releases (it relies on an internal attribute newer bcrypt versions removed).
Calling bcrypt directly is simpler and avoids that broken compatibility layer.
"""

import bcrypt
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict, expires_minutes: int = 60) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Raises jose.JWTError if the token is invalid, tampered with, or expired.
    # Callers (see core/deps.py) are responsible for catching that.
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])