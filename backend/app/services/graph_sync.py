import logging
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from neo4j import AsyncSession as Neo4jAsyncSession

from app.db.models.customer import Customer
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.merchant import Merchant
from app.db.models.organization import Organization

logger = logging.getLogger(__name__)

class GraphSyncService:
    """
    Synchronizes entities from PostgreSQL to Neo4j.
    """
    
    @staticmethod
    async def create_constraints(neo4j_session: Neo4jAsyncSession):
        """Creates unique constraints on Neo4j for performance and deduplication."""
        queries = [
            "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
        ]
        for q in queries:
            await neo4j_session.run(q)
            
    @staticmethod
    async def sync_customers(db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        query = await db.execute(select(Customer))
        customers = query.scalars().all()
        
        cypher = """
        UNWIND $customers AS c
        MERGE (n:Customer {id: c.id})
        SET n.first_name = c.first_name,
            n.last_name = c.last_name,
            n.risk_score = c.risk_score,
            n.country = c.country
        """
        customer_data = [{"id": str(c.id), "first_name": c.first_name, "last_name": c.last_name, "risk_score": c.risk_score, "country": c.country} for c in customers]
        
        if customer_data:
            await neo4j_session.run(cypher, customers=customer_data)
        logger.info(f"Synced {len(customer_data)} customers to Neo4j.")

    @staticmethod
    async def sync_accounts(db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        query = await db.execute(select(Account))
        accounts = query.scalars().all()
        
        cypher = """
        UNWIND $accounts AS a
        MERGE (n:Account {id: a.id})
        SET n.account_number = a.account_number,
            n.account_type = a.account_type,
            n.balance = a.balance,
            n.currency = a.currency
        WITH n, a
        MATCH (c:Customer {id: a.customer_id})
        MERGE (c)-[:OWNS]->(n)
        WITH n, a
        WHERE a.organization_id IS NOT NULL
        MATCH (o:Organization {id: a.organization_id})
        MERGE (n)-[:ASSOCIATED_WITH]->(o)
        """
        account_data = [{
            "id": str(a.id), 
            "account_number": a.account_number, 
            "account_type": a.account_type, 
            "balance": float(a.balance), 
            "currency": a.currency,
            "customer_id": str(a.customer_id),
            "organization_id": str(a.organization_id) if a.organization_id else None
        } for a in accounts]
        
        if account_data:
            await neo4j_session.run(cypher, accounts=account_data)
        logger.info(f"Synced {len(account_data)} accounts to Neo4j.")

    @staticmethod
    async def sync_organizations(db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        query = await db.execute(select(Organization))
        organizations = query.scalars().all()
        
        cypher = """
        UNWIND $organizations AS o
        MERGE (n:Organization {id: o.id})
        SET n.name = o.name,
            n.registration_country = o.registration_country
        """
        org_data = [{"id": str(o.id), "name": o.name, "registration_country": o.registration_country} for o in organizations]
        
        if org_data:
            await neo4j_session.run(cypher, organizations=org_data)
        logger.info(f"Synced {len(org_data)} organizations to Neo4j.")

    @staticmethod
    async def sync_merchants(db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        query = await db.execute(select(Merchant))
        merchants = query.scalars().all()
        
        cypher = """
        UNWIND $merchants AS m
        MERGE (n:Merchant {id: m.id})
        SET n.name = m.name,
            n.category_code = m.category_code,
            n.country = m.country
        """
        merchant_data = [{"id": str(m.id), "name": m.name, "category_code": m.category_code, "country": m.country} for m in merchants]
        
        if merchant_data:
            await neo4j_session.run(cypher, merchants=merchant_data)
        logger.info(f"Synced {len(merchant_data)} merchants to Neo4j.")

    @staticmethod
    async def sync_transactions(db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        # We process transactions in batches if necessary, but here we'll pull all since it's a dev database
        query = await db.execute(select(Transaction))
        transactions = query.scalars().all()
        
        # Account to Account transfer
        transfer_cypher = """
        UNWIND $transactions AS t
        MATCH (src:Account {id: t.source_account_id})
        MATCH (dst:Account {id: t.destination_account_id})
        MERGE (src)-[rel:TRANSFERRED_TO {id: t.id}]->(dst)
        SET rel.amount = t.amount,
            rel.currency = t.currency,
            rel.timestamp = t.timestamp,
            rel.status = t.status
        """
        
        # Account to Merchant
        merchant_cypher = """
        UNWIND $transactions AS t
        MATCH (src:Account {id: t.source_account_id})
        MATCH (m:Merchant {id: t.merchant_id})
        MERGE (src)-[rel:PAID_MERCHANT {id: t.id}]->(m)
        SET rel.amount = t.amount,
            rel.currency = t.currency,
            rel.timestamp = t.timestamp,
            rel.status = t.status
        """
        
        # Withdrawals / Deposits (No explicit destination/merchant in graph, maybe link to a generic external node, 
        # but for now we skip or create generic nodes. Let's just track transfers and merchant payments for typologies)
        
        transfers = []
        merchant_payments = []
        
        for t in transactions:
            data = {
                "id": str(t.id),
                "source_account_id": str(t.source_account_id),
                "amount": float(t.amount),
                "currency": t.currency,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "status": t.status
            }
            if t.destination_account_id:
                data["destination_account_id"] = str(t.destination_account_id)
                transfers.append(data)
            elif t.merchant_id:
                data["merchant_id"] = str(t.merchant_id)
                merchant_payments.append(data)
                
        if transfers:
            await neo4j_session.run(transfer_cypher, transactions=transfers)
        if merchant_payments:
            await neo4j_session.run(merchant_cypher, transactions=merchant_payments)
            
        logger.info(f"Synced {len(transfers)} transfers and {len(merchant_payments)} merchant payments to Neo4j.")

    @classmethod
    async def full_sync(cls, db: AsyncSession, neo4j_session: Neo4jAsyncSession):
        """Perform a full synchronization from Postgres to Neo4j."""
        await cls.create_constraints(neo4j_session)
        await cls.sync_customers(db, neo4j_session)
        await cls.sync_organizations(db, neo4j_session)
        await cls.sync_merchants(db, neo4j_session)
        await cls.sync_accounts(db, neo4j_session)
        await cls.sync_transactions(db, neo4j_session)
        logger.info("Full graph synchronization completed.")
