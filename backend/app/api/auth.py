"""
Registration and login endpoints.

Job: thin HTTP layer only — password hashing lives in core/security.py,
JWT creation lives there too. This file just wires requests to those.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        # New users start at the lowest privilege level by default.
        # Promoting someone to analyst/owner is a deliberate admin action,
        # never something a signup form grants automatically.
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        # Deliberately the SAME error for "no such user" and "wrong password"
        # — telling them apart would let an attacker discover which emails
        # are registered.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}