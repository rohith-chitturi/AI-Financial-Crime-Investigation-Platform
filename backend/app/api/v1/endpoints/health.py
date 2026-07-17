from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api import dependencies
import redis.asyncio as redis
from neo4j import AsyncGraphDatabase
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check() -> Any:
    return {"status": "ok"}

@router.get("/db")
async def db_health_check(db: AsyncSession = Depends(dependencies.get_db)) -> Any:
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection failed")

@router.get("/redis")
async def redis_health_check() -> Any:
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Redis connection failed")

@router.get("/neo4j")
async def neo4j_health_check() -> Any:
    try:
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        await driver.verify_connectivity()
        await driver.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Neo4j connection failed")
