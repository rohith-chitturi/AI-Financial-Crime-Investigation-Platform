from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api import dependencies
from app.db.models.account import Account
from app.schemas.account import AccountList
from app.db.models.user import User

router = APIRouter()

@router.get("/", response_model=AccountList)
async def read_accounts(
    db: AsyncSession = Depends(dependencies.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Retrieve accounts.
    """
    query = select(Account)

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(total_query)
    total_count = total.scalar_one()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    accounts = result.scalars().all()

    return {
        "items": accounts,
        "total": total_count,
        "page": (skip // limit) + 1,
        "size": limit
    }
