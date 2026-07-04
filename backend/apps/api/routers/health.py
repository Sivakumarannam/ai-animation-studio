from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from apps.api.config import get_settings
from database.connection import get_session

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": get_settings().APP_NAME,
        "version": get_settings().APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/healthz/db")
async def health_db() -> dict[str, Any]:
    try:
        async for session in get_session():
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/healthz/ready")
async def ready() -> dict[str, Any]:
    return {"status": "ready"}
