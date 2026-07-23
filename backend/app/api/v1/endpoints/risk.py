from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Any
import uuid

from app.db.database import get_db
from app.api.dependencies import get_current_active_user
from app.db.models.user import User
from app.db.models.risk_analysis import TransactionRiskAnalysis
from app.schemas.risk import TransactionRiskAnalysisResponse
from app.services.risk_scoring import RiskScoringService

from app.db.neo4j_database import get_neo4j_session
from neo4j import AsyncSession as Neo4jAsyncSession

router = APIRouter()

@router.post("/analyze/{transaction_id}", response_model=TransactionRiskAnalysisResponse)
async def analyze_transaction(
    transaction_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    neo4j_session: Neo4jAsyncSession = Depends(get_neo4j_session),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Manually triggers the risk engine for a given transaction.
    """
    try:
        analysis = await RiskScoringService.analyze_transaction(db, neo4j_session, str(transaction_id), background_tasks)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{transaction_id}", response_model=TransactionRiskAnalysisResponse)
async def get_transaction_analysis(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieves the existing risk analysis for a transaction.
    """
    result = await db.execute(
        select(TransactionRiskAnalysis).where(TransactionRiskAnalysis.transaction_id == str(transaction_id))
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Risk analysis not found for this transaction.")
        
    return analysis
