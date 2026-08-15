"""
Encrypts and decrypts database connection strings before they touch
Querynetic's own app database. Uses Fernet — symmetric encryption from the
`cryptography` package (already a dependency via python-jose[cryptography]).

Rule this file enforces: a database connection string (which contains a
password) is NEVER stored in plain text, anywhere.
"""

from cryptography.fernet import Fernet
from app.core.config import settings

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_string(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_string(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()