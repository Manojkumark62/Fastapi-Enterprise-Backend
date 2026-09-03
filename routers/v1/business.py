from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.auth import get_current_active_user
from dependencies.db import get_db
from models.user import User
from schemas.business import BusinessDashboardResponse
from services.business_dashboard_service import BusinessDashboardService

router = APIRouter(prefix="/business", tags=["Business management"])


@router.get("/dashboard", response_model=BusinessDashboardResponse)
def dashboard(
    actor: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return BusinessDashboardService(db).summary(actor.id)