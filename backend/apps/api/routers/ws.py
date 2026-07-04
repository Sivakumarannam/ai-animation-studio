"""
WebSocket router — real-time progress notifications for running workflows.

Clients connect to /api/v1/ws/progress/{run_id} and receive JSON events:
  {
    "run_id": "...",
    "step": "story_generation",
    "percent": 28.5,
    "message": "Generating story script with LLM",
    "status": "running" | "completed" | "failed",
    "timestamp": "2026-...",
  }
"""
from __future__ import annotations

import asyncio
import os

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

logger = structlog.get_logger()

router = APIRouter(tags=["websocket"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@router.websocket("/ws/progress/{run_id}")
async def workflow_progress(websocket: WebSocket, run_id: str) -> None:
    """
    Stream workflow progress events to the client.

    The client stays connected until:
    - The workflow reaches a terminal state (completed / failed / cancelled)
    - The client disconnects
    - A 60-second idle timeout fires (no new events)
    """
    await websocket.accept()
    logger.info("ws_client_connected", run_id=run_id)

    from workflow.progress import get_progress_tracker
    tracker = get_progress_tracker(REDIS_URL)

    idle_timeout = 60.0  # seconds — close if no events
    try:
        async for event in tracker.subscribe(run_id):
            try:
                await asyncio.wait_for(
                    websocket.send_json(event),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                logger.warning("ws_send_timeout", run_id=run_id)
                break

            # Close after terminal state so the client knows we're done
            status_val = event.get("status", "")
            if status_val in ("completed", "failed", "cancelled"):
                await asyncio.sleep(0.5)  # let the last message arrive
                break

    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", run_id=run_id)
    except Exception as exc:
        logger.error("ws_error", run_id=run_id, error=str(exc))
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info("ws_connection_closed", run_id=run_id)


@router.websocket("/ws/ping")
async def ws_ping(websocket: WebSocket) -> None:
    """Simple keepalive endpoint for connection testing."""
    await websocket.accept()
    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
