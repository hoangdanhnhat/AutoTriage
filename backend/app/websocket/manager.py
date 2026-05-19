"""
WebSocket connection manager with Redis pub/sub broadcast.

Each job gets a channel `triage:<job_id>`.
When the Ansible runner publishes to Redis, this manager forwards
the message to all WebSocket clients watching that job.
"""
import asyncio
import json
import logging
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # job_id -> set of active WebSocket connections
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._pubsub_tasks: dict[int, asyncio.Task] = {}
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def connect(self, websocket: WebSocket, job_id: int) -> None:
        await websocket.accept()
        self._connections[job_id].add(websocket)
        # Start subscriber task if not already running for this job
        if job_id not in self._pubsub_tasks or self._pubsub_tasks[job_id].done():
            task = asyncio.create_task(self._subscribe(job_id))
            self._pubsub_tasks[job_id] = task

    def disconnect(self, websocket: WebSocket, job_id: int) -> None:
        self._connections[job_id].discard(websocket)
        if not self._connections[job_id]:
            # No more listeners — cancel subscriber
            task = self._pubsub_tasks.pop(job_id, None)
            if task and not task.done():
                task.cancel()

    async def broadcast(self, job_id: int, message: dict) -> None:
        dead: set[WebSocket] = set()
        for ws in list(self._connections.get(job_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws, job_id)

    async def _subscribe(self, job_id: int) -> None:
        channel = f"triage:{job_id}"
        redis = await self._get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for raw_message in pubsub.listen():
                if raw_message["type"] != "message":
                    continue
                if not self._connections.get(job_id):
                    break
                try:
                    data = json.loads(raw_message["data"])
                    await self.broadcast(job_id, data)
                except (json.JSONDecodeError, Exception) as exc:
                    logger.warning("WS broadcast error for job %d: %s", job_id, exc)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)


manager = ConnectionManager()
