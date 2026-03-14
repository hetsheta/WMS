from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.models import User

bearer = HTTPBearer()


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await get_current_user(db, credentials.credentials)


async def superuser(user: User = Depends(current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required")
    return user
