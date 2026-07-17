from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
import random
from typing import List
from datetime import datetime, timedelta

from app.db.models.account import Account
from app.db.models.merchant import Merchant
from app.db.models.transaction import Transaction

async def generate_normal_transactions(
    db: AsyncSession, 
    fake: Faker, 
    accounts: List[Account], 
    merchants: List[Merchant], 
    start_date: datetime,
    end_date: datetime
) -> List[Transaction]:
    transactions = []
    
    for account in accounts:
        # Generate 5-20 normal transactions per account
        num_transactions = random.randint(5, 20)
        
        for _ in range(num_transactions):
            # Normal transactions are usually smaller amounts, standard times
            amount = round(random.uniform(10.0, 1500.0), 2)
            
            # Random date between start_date and end_date
            delta = end_date - start_date
            random_days = random.randrange(delta.days)
            transaction_date = start_date + timedelta(days=random_days, hours=random.randint(8, 20))

            merchant = random.choice(merchants)
            
            transaction = Transaction(
                source_account_id=account.id,
                destination_account_id=None,
                merchant_id=merchant.id,
                amount=amount,
                transaction_type="payment",
                status="completed",
                timestamp=transaction_date,
                location_country=merchant.country,
                is_suspicious_ground_truth=False
            )
            transactions.append(transaction)
            
            # Update balances roughly
            account.balance = float(account.balance) - amount

    db.add_all(transactions)
    await db.commit()
    return transactions
