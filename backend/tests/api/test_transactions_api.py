import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.api.dependencies import get_current_active_user
from app.db.models.transaction import Transaction
from app.db.models.user import User
from app.db.database import AsyncSessionLocal
from datetime import datetime
import uuid

async def override_get_current_active_user():
    return User(id=uuid.uuid4(), email="test@example.com", is_active=True)

@pytest.mark.asyncio
async def test_transactions_ground_truth_isolation(async_client: AsyncClient):
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    async with AsyncSessionLocal() as db_session:
        # Insert a suspicious transaction directly to DB
        tx = Transaction(
            amount=5000.0,
            transaction_type="transfer",
            status="completed",
            timestamp=datetime.utcnow(),
            is_suspicious_ground_truth=True,
            suspicious_pattern_type="TEST_PATTERN"
        )
        db_session.add(tx)
        await db_session.commit()

    # Fetch transactions via API
    response = await async_client.get("/api/v1/transactions/")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data["items"]) > 0
    
    # Check that ground truth fields are excluded
    # We can check the first item to ensure it's not there
    for api_tx in data["items"]:
        assert "is_suspicious_ground_truth" not in api_tx
        assert "suspicious_pattern_type" not in api_tx
