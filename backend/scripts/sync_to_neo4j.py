import asyncio
import logging
import sys
import os

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.neo4j_database import neo4j_db
from app.services.graph_sync import GraphSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing Neo4j connection...")
    await neo4j_db.connect()
    
    if not neo4j_db.driver:
        logger.error("Failed to connect to Neo4j. Exiting.")
        return
        
    logger.info("Starting graph synchronization from PostgreSQL...")
    
    try:
        async with SessionLocal() as db_session:
            async with neo4j_db.driver.session() as neo4j_session:
                await GraphSyncService.full_sync(db_session, neo4j_session)
                
        logger.info("Graph synchronization completed successfully.")
    except Exception as e:
        logger.error(f"Error during synchronization: {str(e)}")
    finally:
        await neo4j_db.close()

if __name__ == "__main__":
    asyncio.run(main())
