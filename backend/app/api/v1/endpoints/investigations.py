import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models.investigation import Investigation, AgentExecution
from app.db.models.transaction import Transaction
from app.db.models.risk_analysis import TransactionRiskAnalysis
from app.schemas.investigation import InvestigationResponse
from app.agents.workflow import investigation_graph
from app.agents.state import InvestigationState

router = APIRouter()

async def run_investigation_task(
    transaction_id: uuid.UUID, 
    trigger_source: str
):
    """
    Background task to run the LangGraph workflow and persist the results.
    """
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy.orm import joinedload
            stmt = select(Transaction).options(joinedload(Transaction.source_account)).where(Transaction.id == transaction_id)
            result = await db.execute(stmt)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                print(f"Investigation failed: Transaction {transaction_id} not found.")
                return

            risk_stmt = select(TransactionRiskAnalysis).where(TransactionRiskAnalysis.transaction_id == transaction_id).order_by(TransactionRiskAnalysis.analysis_timestamp.desc())
            risk_result = await db.execute(risk_stmt)
            risk_analysis = risk_result.scalars().first()

            # Build initial state
            initial_state: InvestigationState = {
                "investigation_id": str(uuid.uuid4()),
                "transaction_id": str(transaction_id),
                "customer_id": str(transaction.source_account.customer_id) if transaction.source_account else "",
                "alert_id": None,
                "risk_analysis_id": str(risk_analysis.id) if risk_analysis else None,
                "trigger_source": trigger_source,
                "ml_score": float(risk_analysis.ml_score) if risk_analysis else 0.0,
                "aml_findings": risk_analysis.triggered_rules if risk_analysis else [],
                "graph_findings": {"score": float(risk_analysis.graph_score), "evidence": risk_analysis.graph_evidence} if risk_analysis and risk_analysis.graph_score else {},
                "customer_summary": {"previous_risk_score": float(risk_analysis.unified_risk_score)} if risk_analysis else {},
                "regulatory_summary": None,
                "evidence": "",
                "recommendations": [],
                "confidence_score": 0.0,
                "report_markdown": "",
                "processing_log": [],
                "execution_metadata": {},
                "errors": []
            }

            # Create Database Record Initial State
            inv_record = Investigation(
                id=uuid.UUID(initial_state["investigation_id"]),
                transaction_id=transaction_id,
                customer_id=uuid.UUID(initial_state["customer_id"]) if initial_state["customer_id"] else None,
                trigger_source=trigger_source,
                status="IN_PROGRESS"
            )
            db.add(inv_record)
            await db.commit()

            # Execute Graph
            final_state = await investigation_graph.ainvoke(initial_state)

            # Update Investigation Record
            inv_record.status = "COMPLETED" if not final_state.get("errors") else "COMPLETED_WITH_ERRORS"
            inv_record.summary = final_state.get("evidence", "")
            inv_record.recommendations = final_state.get("recommendations", [])
            inv_record.confidence_score = final_state.get("confidence_score", 0.0)
            inv_record.report_markdown = final_state.get("report_markdown", "")
            inv_record.errors = final_state.get("errors", [])
            
            # Insert Agent Executions
            processing_log = final_state.get("processing_log", [])
            for log in processing_log:
                execution = AgentExecution(
                    investigation_id=inv_record.id,
                    agent_name=log.get("agent_name"),
                    prompt_version=log.get("prompt_version"),
                    model_version=log.get("model_version"),
                    latency_ms=log.get("latency_ms"),
                    status=log.get("status"),
                    output_summary=log.get("output_summary"),
                    error_details=log.get("error_details")
                )
                db.add(execution)
                
            await db.commit()

        except Exception as e:
            print(f"Investigation background task failed: {e}")
        # Need to mark it failed if we can
        # For simplicity, we just print here. In production, we'd log and update the DB row.


@router.post("/run/{transaction_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_investigation(
    transaction_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Manually triggers an investigation for a specific transaction.
    """
    # Verify transaction exists
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Transaction not found")

    background_tasks.add_task(run_investigation_task, transaction_id, "MANUAL")
    return {"message": "Investigation triggered successfully.", "transaction_id": transaction_id}


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieves a specific investigation by ID, including its agent execution logs.
    """
    from sqlalchemy.orm import selectinload
    stmt = select(Investigation).options(selectinload(Investigation.agent_executions)).where(Investigation.id == investigation_id)
    result = await db.execute(stmt)
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieves a paginated list of investigations.
    """
    from sqlalchemy.orm import selectinload
    stmt = select(Investigation).options(selectinload(Investigation.agent_executions)).order_by(Investigation.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
