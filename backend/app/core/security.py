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
from cryptography.fernet import Fernet
from app.core.config import settings


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# Separate from password hashing: this is REVERSIBLE encryption, used only
# for database connection strings — we need the real credential back to
# actually connect, unlike a password hash, which never needs to be undone.
_fernet = Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))


def encrypt_string(plain_text: str) -> str:
    return _fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_string(encrypted_text: str) -> str:
    return _fernet.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # "type" claim lets every endpoint verify it received the KIND of
    # token it expects — an access token can't be used as a refresh token
    # even though both are just JWTs, and vice versa.
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Raises jose.JWTError if the token is invalid, tampered with, or expired.
    # Callers (see core/deps.py) are responsible for catching that.
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])