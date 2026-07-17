from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker
import random
from typing import List, Dict

from app.db.models.customer import Customer
from app.db.models.account import Account
from app.db.models.merchant import Merchant
from app.db.models.organization import Organization

async def generate_customers(db: AsyncSession, fake: Faker, num_customers: int) -> List[Customer]:
    customers = []
    for _ in range(num_customers):
        customer = Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            email=fake.unique.email(),
            phone_number=fake.phone_number(),
            address=fake.address(),
            country=fake.country(),
            risk_score=random.uniform(0.0, 0.3) # Initial low baseline
        )
        customers.append(customer)
    
    db.add_all(customers)
    await db.commit()
    # Refresh to get IDs
    for c in customers:
        await db.refresh(c)
    return customers

async def generate_accounts(db: AsyncSession, fake: Faker, customers: List[Customer]) -> List[Account]:
    accounts = []
    for customer in customers:
        # Each customer gets 1 to 3 accounts
        num_accounts = random.randint(1, 3)
        for _ in range(num_accounts):
            account = Account(
                customer_id=customer.id,
                account_number=fake.unique.bban(),
                account_type=random.choice(["checking", "savings"]),
                balance=random.uniform(100.0, 50000.0),
                currency="USD"
            )
            accounts.append(account)

    db.add_all(accounts)
    await db.commit()
    for a in accounts:
        await db.refresh(a)
    return accounts

async def generate_merchants(db: AsyncSession, fake: Faker, num_merchants: int) -> List[Merchant]:
    merchants = []
    categories = ["retail", "grocery", "software", "entertainment", "travel", "restaurant"]
    for _ in range(num_merchants):
        merchant = Merchant(
            name=fake.company(),
            category=random.choice(categories),
            country=fake.country()
        )
        merchants.append(merchant)
        
    db.add_all(merchants)
    await db.commit()
    for m in merchants:
        await db.refresh(m)
    return merchants

async def generate_organizations(db: AsyncSession, fake: Faker, num_orgs: int) -> List[Organization]:
    orgs = []
    industries = ["technology", "finance", "healthcare", "real_estate", "logistics"]
    for _ in range(num_orgs):
        org = Organization(
            name=fake.company(),
            industry=random.choice(industries),
            country=fake.country()
        )
        orgs.append(org)

    db.add_all(orgs)
    await db.commit()
    for o in orgs:
        await db.refresh(o)
    return orgs
