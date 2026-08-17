"""
FastAPI dependencies for authentication and role-based access control.

get_current_user: verifies the JWT on every request, loads the real user.
require_role: a dependency FACTORY — call it with a minimum role, and it
returns a dependency that only lets that role or higher through.

Role hierarchy is rank-based, not an exact match: require_role("analyst")
correctly allows both "analyst" AND "owner" — we compare rank, not identity.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.db import get_db
from app.models.user import User

# HTTPBearer (not OAuth2PasswordBearer) — this matches what we actually
# built: log in separately via /api/auth/login (JSON body), get a token
# back, then present that token on later requests. Swagger's "Authorize"
# dialog for this scheme is a single "paste your token" field, not a
# username/password form trying to fetch one for you.
bearer_scheme = HTTPBearer()

ROLE_HIERARCHY = {"viewer": 0, "analyst": 1, "owner": 2}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong token type — expected an access token",
            )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def require_role(minimum_role: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_rank = ROLE_HIERARCHY.get(current_user.role, -1)
        required_rank = ROLE_HIERARCHY.get(minimum_role, 99)

        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role}' role or higher.",
            )
        return current_user

    return role_checker