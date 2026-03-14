from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import current_user
from app.models.models import User
from app.schemas.schemas import DashboardStats
from app.services.operations import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    stats = await get_dashboard_stats(db, user.id)
    return DashboardStats(**stats)
