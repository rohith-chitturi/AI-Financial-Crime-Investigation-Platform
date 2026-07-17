import pytest
from faker import Faker
from datetime import datetime

from app.db.models.customer import Customer
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.database import AsyncSessionLocal
from scripts.generators.faker_config import get_faker
from scripts.generators.entities import generate_customers, generate_accounts
from scripts.generators.suspicious_transactions import generate_structuring

@pytest.mark.asyncio
async def test_reproducibility():
    # Ensure get_faker() returns the same data for two independent calls
    fake1 = get_faker()
    fake2 = get_faker()
    
    assert fake1.name() == fake2.name()
    assert fake1.email() == fake2.email()

@pytest.mark.asyncio
async def test_generate_structuring_typology():
    # Use a random seed for the test to avoid colliding with seed 42 data in the DB
    fake = Faker()
    
    async with AsyncSessionLocal() as db_session:
        # Generate mock data
        customers = await generate_customers(db_session, fake, 1)
        accounts = await generate_accounts(db_session, fake, customers)
        
        assert len(accounts) > 0
        start_date = datetime.utcnow()
        
        # Generate structuring
        transactions = await generate_structuring(db_session, fake, accounts, start_date)
        
        assert len(transactions) >= 4
        
        # Verify ground truth labels are set correctly in DB
        for tx in transactions:
            assert tx.is_suspicious_ground_truth is True
            assert tx.suspicious_pattern_type == "STRUCTURING"
            assert 9000.0 <= float(tx.amount) <= 9900.0

