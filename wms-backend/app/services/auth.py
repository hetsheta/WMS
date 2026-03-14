import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.models import User
from app.schemas.schemas import TokenResponse, UserRegister


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        id=uuid.uuid4(),
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user


def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


async def issue_password_reset_token(db: AsyncSession, email: str) -> dict:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        return {"message": "If the account exists, a reset token was generated"}
    reset_token = create_access_token(str(user.id), expires_delta=timedelta(minutes=30))
    return {
        "message": "If the account exists, a reset token was generated",
        "reset_token": reset_token,
    }


async def reset_password(db: AsyncSession, token: str, new_password: str) -> dict:
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "Password reset successful"}


async def get_current_user(db: AsyncSession, token: str) -> User:
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user
