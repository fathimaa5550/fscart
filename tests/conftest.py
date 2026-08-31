"""
Shared pytest fixtures for the fscart test suite.

Each test function receives a fresh in-memory SQLite database so tests are
completely isolated from one another.
"""
import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import create_app

# ──────────────────────────────────────────────────────────────────────────────
# In-memory SQLite test engine
# ──────────────────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    Yield a TestClient whose database is a fresh in-memory SQLite instance.
    All tables are created before each test and dropped afterwards.
    """
    # Create a per-test async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def _setup() -> None:
        """Create all tables in the in-memory database."""
        # Import all models so their table metadata is populated on Base
        from app.models import product, cart, order  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown() -> None:
        """Drop all tables and dispose the engine."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    # Override the get_db dependency to use the test database
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Run setup using asyncio.run() — works on Python 3.10+ including 3.14
    asyncio.run(_setup())

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # Teardown
    asyncio.run(_teardown())
