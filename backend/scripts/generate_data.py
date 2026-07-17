import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend directory to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal
from generators.faker_config import get_faker
from generators.entities import generate_customers, generate_accounts, generate_merchants, generate_organizations
from generators.normal_transactions import generate_normal_transactions
from generators.suspicious_transactions import generate_structuring, generate_circular_funds

async def main():
    print("Starting Synthetic Banking Data Generation...")
    
    fake = get_faker()
    
    async with AsyncSessionLocal() as db:
        print("Generating Entities...")
        customers = await generate_customers(db, fake, num_customers=100)
        accounts = await generate_accounts(db, fake, customers)
        merchants = await generate_merchants(db, fake, num_merchants=50)
        orgs = await generate_organizations(db, fake, num_orgs=20)
        print(f"Generated {len(customers)} customers, {len(accounts)} accounts, {len(merchants)} merchants, {len(orgs)} organizations.")
        
        # We need to reload accounts with their customer relation loaded for country logic
        # But our simple script can just rely on basic data or fetch them. For simplicity, we assume we just pass accounts
        from sqlalchemy.future import select
        from sqlalchemy.orm import selectinload
        from app.db.models.account import Account
        
        result = await db.execute(select(Account).options(selectinload(Account.customer)))
        accounts_with_customers = result.scalars().all()
        
        print("Generating Normal Transactions...")
        start_date = datetime.utcnow() - timedelta(days=180)
        end_date = datetime.utcnow()
        await generate_normal_transactions(db, fake, accounts_with_customers, merchants, start_date, end_date)
        
        print("Injecting Suspicious Typologies...")
        # Inject Structuring pattern
        await generate_structuring(db, fake, accounts_with_customers, start_date)
        
        # Inject Circular Funds pattern
        await generate_circular_funds(db, fake, list(accounts_with_customers), start_date + timedelta(days=30))
        
        print("Data Generation Complete!")

if __name__ == "__main__":
    asyncio.run(main())
