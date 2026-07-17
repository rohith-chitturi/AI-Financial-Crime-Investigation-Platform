from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api import dependencies
from app.db.models.customer import Customer
from app.schemas.customer import CustomerList, CustomerResponse
from app.db.models.user import User

router = APIRouter()

@router.get("/", response_model=CustomerList)
async def read_customers(
    db: AsyncSession = Depends(dependencies.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Retrieve customers.
    """
    query = select(Customer)
    if search:
        search_filter = Customer.first_name.ilike(f"%{search}%") | Customer.last_name.ilike(f"%{search}%") | Customer.email.ilike(f"%{search}%")
        query = query.where(search_filter)

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(total_query)
    total_count = total.scalar_one()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()

    return {
        "items": customers,
        "total": total_count,
        "page": (skip // limit) + 1,
        "size": limit
    }
