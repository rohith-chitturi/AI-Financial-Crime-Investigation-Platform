import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime
import uuid

from app.main import app
from app.db.database import AsyncSessionLocal
from app.api.dependencies import get_current_active_user
from app.db.models.user import User
from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.db.models.customer import Customer
from app.db.models.alert import Alert
from app.db.models.risk_analysis import TransactionRiskAnalysis

from app.ml.feature_engineering import FeatureEngineer
from app.services.risk_scoring import RiskScoringService
from scripts.generators.faker_config import get_faker

async def override_get_current_active_user():
    return User(id=uuid.uuid4(), email="test@example.com", is_active=True)

@pytest.fixture
def mock_auth():
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_feature_engineering_no_future_leakage():
    async with AsyncSessionLocal() as db:
        # Create a mock customer and account
        customer = Customer(first_name="Test", last_name="User", date_of_birth=datetime(1990, 1, 1).date(), email=f"test_risk_{uuid.uuid4()}@example.com", country="US")
        db.add(customer)
        await db.commit()
        
        account = Account(customer_id=customer.id, account_number=f"ACC_{uuid.uuid4()}", account_type="checking", balance=1000.0)
        db.add(account)
        await db.commit()
        
        # Create past transaction
        past_tx = Transaction(
            source_account_id=account.id, amount=100.0, transaction_type="transfer", 
            timestamp=datetime(2023, 1, 1, 10, 0, 0)
        )
        db.add(past_tx)
        
        # Create current transaction
        current_tx = Transaction(
            source_account_id=account.id, amount=200.0, transaction_type="transfer",
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        db.add(current_tx)
        
        # Create future transaction (should be ignored)
        future_tx = Transaction(
            source_account_id=account.id, amount=5000.0, transaction_type="transfer",
            timestamp=datetime(2023, 1, 2, 10, 0, 0)
        )
        db.add(future_tx)
        await db.commit()
        
        # Extract features for current_tx
        features = await FeatureEngineer.compute_features_for_transaction(db, current_tx)
        
        # Verify it only saw the past transaction
        assert features["tx_24h_count"] == 1.0
        assert features["historical_avg_amount"] == 100.0
        assert features["transaction_amount"] == 200.0

@pytest.mark.asyncio
async def test_duplicate_alert_prevention():
    async with AsyncSessionLocal() as db:
        # Setup mock data
        customer = Customer(first_name="Alert", last_name="User", date_of_birth=datetime(1990, 1, 1).date(), email=f"alert_{uuid.uuid4()}@example.com", country="US")
        db.add(customer)
        await db.commit()
        account = Account(customer_id=customer.id, account_number=f"ACC_{uuid.uuid4()}", account_type="checking", balance=1000.0)
        db.add(account)
        await db.commit()
        
        tx = Transaction(
            source_account_id=account.id, amount=9999.0, transaction_type="transfer"
        )
        db.add(tx)
        await db.commit()
        
        # Analyze once (should create alert if score >= 75)
        # We'll artificially set the score high via ML mock or just let the structuring rule catch it if we add history
        # Let's bypass RiskScoringService logic and test the private alert generator directly
        
        analysis = TransactionRiskAnalysis(
            transaction_id=tx.id, model_version="1.0.0",
            ml_score=80.0, aml_rule_score=80.0, customer_risk_score=50.0,
            unified_risk_score=90.0, risk_level="Critical",
            explanation="Test", triggered_rules=[]
        )
        
        # Call internal alert creation twice
        await RiskScoringService._create_or_update_alert(db, tx, analysis)
        await RiskScoringService._create_or_update_alert(db, tx, analysis)
        
        # Check that only one alert exists
        from sqlalchemy.future import select
        from sqlalchemy import func
        count_query = await db.execute(select(func.count()).select_from(Alert).where(Alert.transaction_id == tx.id))
        count = count_query.scalar_one()
        assert count == 1

@pytest.mark.asyncio
async def test_risk_api_endpoints(async_client: AsyncClient, mock_auth):
    # This requires an existing transaction ID
    async with AsyncSessionLocal() as db:
        customer = Customer(first_name="API", last_name="User", date_of_birth=datetime(1990, 1, 1).date(), email=f"api_{uuid.uuid4()}@example.com", country="US")
        db.add(customer)
        await db.commit()
        account = Account(customer_id=customer.id, account_number=f"ACC_{uuid.uuid4()}", account_type="checking", balance=1000.0)
        db.add(account)
        await db.commit()
        
        tx = Transaction(source_account_id=account.id, amount=100.0, transaction_type="deposit")
        db.add(tx)
        await db.commit()
        tx_id = str(tx.id)
        
    # Test POST /api/v1/risk/analyze/{id}
    response = await async_client.post(f"/api/v1/risk/analyze/{tx_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "unified_risk_score" in data
    assert "explanation" in data
    
    # Test GET /api/v1/risk/analysis/{id}
    response2 = await async_client.get(f"/api/v1/risk/analysis/{tx_id}")
    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["id"] == data["id"]
    
    # Test GET /api/v1/alerts/
    response3 = await async_client.get("/api/v1/alerts/")
    assert response3.status_code == status.HTTP_200_OK
    assert "items" in response3.json()
