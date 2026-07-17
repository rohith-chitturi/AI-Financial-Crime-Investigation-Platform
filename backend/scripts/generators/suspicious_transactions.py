from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
import random
from typing import List
from datetime import datetime, timedelta

from app.db.models.account import Account
from app.db.models.transaction import Transaction

async def generate_structuring(
    db: AsyncSession, 
    fake: Faker, 
    accounts: List[Account], 
    start_date: datetime
) -> List[Transaction]:
    """
    Inject structuring typology: Multiple deposits just under reporting threshold (e.g., $10k in US).
    """
    transactions = []
    
    # Pick a random account to act suspiciously
    suspicious_account = random.choice(accounts)
    
    # 4 to 6 transactions just under $10,000 within a few days
    num_txs = random.randint(4, 6)
    current_date = start_date
    
    for _ in range(num_txs):
        amount = round(random.uniform(9000.0, 9900.0), 2)
        current_date += timedelta(hours=random.randint(2, 48))
        
        transaction = Transaction(
            source_account_id=None, # Cash deposit
            destination_account_id=suspicious_account.id,
            amount=amount,
            transaction_type="deposit",
            status="completed",
            timestamp=current_date,
            location_country="US",
            is_suspicious_ground_truth=True,
            suspicious_pattern_type="STRUCTURING"
        )
        transactions.append(transaction)
        suspicious_account.balance = float(suspicious_account.balance) + amount

    db.add_all(transactions)
    await db.commit()
    return transactions

async def generate_circular_funds(
    db: AsyncSession, 
    fake: Faker, 
    accounts: List[Account], 
    start_date: datetime
) -> List[Transaction]:
    """
    Inject circular funds typology: A -> B -> C -> A
    """
    transactions = []
    if len(accounts) < 3:
        return []
    
    # Pick 3 random distinct accounts
    actors = random.sample(accounts, 3)
    A, B, C = actors[0], actors[1], actors[2]
    
    amount = round(random.uniform(20000.0, 50000.0), 2)
    current_date = start_date
    
    flow = [(A, B), (B, C), (C, A)]
    
    for src, dst in flow:
        current_date += timedelta(hours=random.randint(1, 12))
        
        # Slight variation in amount for fees or layering
        transfer_amount = amount - round(random.uniform(10.0, 100.0), 2)
        amount = transfer_amount
        
        transaction = Transaction(
            source_account_id=src.id,
            destination_account_id=dst.id,
            amount=transfer_amount,
            transaction_type="transfer",
            status="completed",
            timestamp=current_date,
            location_country=src.customer.country, # assuming loaded
            is_suspicious_ground_truth=True,
            suspicious_pattern_type="CIRCULAR_FUNDS"
        )
        transactions.append(transaction)
        src.balance = float(src.balance) - transfer_amount
        dst.balance = float(dst.balance) + transfer_amount

    db.add_all(transactions)
    await db.commit()
    return transactions
