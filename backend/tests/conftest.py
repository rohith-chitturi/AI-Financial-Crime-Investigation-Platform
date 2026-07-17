import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from app.main import app

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
