from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, customers, accounts, transactions, risk, alerts, graph, investigations

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk engine"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(graph.router, prefix="/graph", tags=["knowledge graph"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["investigations"])

