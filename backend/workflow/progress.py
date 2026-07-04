"""
ProgressTracker — publishes workflow progress to Redis pub/sub.
FastAPI WebSocket clients subscribe to run_id channels and receive real-time updates.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class ProgressTracker:
    """
    Publishes progress events to Redis channel: `workflow:progress:<run_id>`.
    The WebSocket router subscribes to these channels and forwards to clients.
    """

    CHANNEL_PREFIX = "workflow:progress:"
    STATE_KEY_PREFIX = "workflow:state:"
    STATE_TTL = 86400  # 24 hours

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._redis: Any = None

    async def _get_redis(self) -> Any:
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def publish(
        self,
        run_id: str,
        step_name: str,
        percent: float,
        message: str,
        status: str = "running",
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Publish a progress event to the run_id channel."""
        payload: dict[str, Any] = {
            "run_id": run_id,
            "step": step_name,
            "percent": round(percent, 1),
            "message": message,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            payload.update(extra)
        channel = f"{self.CHANNEL_PREFIX}{run_id}"
        try:
            r = await self._get_redis()
            await r.publish(channel, json.dumps(payload))
            # Also store the latest snapshot in a key for late-joining clients
            await r.setex(
                f"{self.STATE_KEY_PREFIX}{run_id}",
                self.STATE_TTL,
                json.dumps(payload),
            )
        except Exception:
            pass  # Progress failures must never crash the pipeline

    async def get_latest(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve the most recent progress snapshot for a run_id."""
        try:
            r = await self._get_redis()
            raw = await r.get(f"{self.STATE_KEY_PREFIX}{run_id}")
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def subscribe(self, run_id: str):
        """
        Async generator that yields progress events for a run_id.
        Use in WebSocket handlers.
        """
        import asyncio
        import redis.asyncio as aioredis

        r = aioredis.from_url(self._redis_url, decode_responses=True)
        pubsub = r.pubsub()
        channel = f"{self.CHANNEL_PREFIX}{run_id}"
        await pubsub.subscribe(channel)
        try:
            # Yield last known state immediately so connecting clients aren't blank
            latest = await self.get_latest(run_id)
            if latest:
                yield latest

            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg["type"] == "message":
                    yield json.loads(msg["data"])
                else:
                    await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_tracker: ProgressTracker | None = None


def get_progress_tracker(redis_url: str = "redis://localhost:6379/0") -> ProgressTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker(redis_url=redis_url)
    return _tracker
