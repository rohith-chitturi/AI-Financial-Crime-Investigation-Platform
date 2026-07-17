from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Any, Optional
import uuid

from app.db.database import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.user import User
from app.db.models.alert import Alert
from app.schemas.risk import AlertResponse, AlertListResponse

router = APIRouter()

@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_level: Optional[str] = None
) -> Any:
    """
    Retrieve alerts.
    """
    query = select(Alert)
    count_query = select(func.count()).select_from(Alert)
    
    if status_filter:
        query = query.where(Alert.status == status_filter)
        count_query = count_query.where(Alert.status == status_filter)
        
    if risk_level:
        query = query.where(Alert.risk_level == risk_level)
        count_query = count_query.where(Alert.risk_level == risk_level)
        
    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    
    total = await db.execute(count_query)
    total_count = total.scalar_one()
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return {
        "items": alerts,
        "total": total_count,
        "page": skip // limit + 1,
        "size": limit
    }

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve specific alert details.
    """
    result = await db.execute(select(Alert).where(Alert.id == str(alert_id)))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return alert
