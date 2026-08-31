from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Liveness probe",
    description="Returns 200 when the application process is alive.",
    response_description="Application health status",
)
async def health() -> dict:
    """Kubernetes-style liveness probe — always 200 while the process runs."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Returns 200 when the application is ready to serve traffic (database is reachable).",
    response_description="Application readiness status",
)
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Kubernetes-style readiness probe.
    Executes a lightweight SQL statement to confirm the database is reachable.
    Returns 503 (raises an exception) if the DB is unavailable.
    """
    await db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "database": "connected",
    }
