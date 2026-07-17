from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from app.api import dependencies
from app.db.models.transaction import Transaction
from app.schemas.transaction import TransactionList
from app.db.models.user import User

router = APIRouter()

@router.get("/", response_model=TransactionList)
async def read_transactions(
    db: AsyncSession = Depends(dependencies.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    account_id: Optional[str] = None,
    sort_by_amount: Optional[str] = Query(None, regex="^(asc|desc)$"),
    current_user: User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Retrieve transactions.
    Ground-truth labels for ML evaluation are NOT exposed through this API.
    """
    query = select(Transaction)
    
    if account_id:
        query = query.where(
            (Transaction.source_account_id == account_id) | 
            (Transaction.destination_account_id == account_id)
        )
        
    if sort_by_amount == "desc":
        query = query.order_by(desc(Transaction.amount))
    elif sort_by_amount == "asc":
        query = query.order_by(Transaction.amount)
    else:
        # Default sort by timestamp desc
        query = query.order_by(desc(Transaction.timestamp))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(total_query)
    total_count = total.scalar_one()

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()

    return {
        "items": transactions,
        "total": total_count,
        "page": (skip // limit) + 1,
        "size": limit
    }
