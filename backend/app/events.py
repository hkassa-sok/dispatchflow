import asyncio
import json
import logging
import os
from redis.asyncio import Redis

class Events:
    def __init__(self):
        self.clients = set()
        self.redis = None
        self.task = None
    async def start(self):
        url = os.getenv("REDIS_URL")
        if url:
            self.redis = Redis.from_url(url, decode_responses=True)
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("dispatchflow")
            self.task = asyncio.create_task(self.listen())
    async def listen(self):
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                await self.broadcast(message["data"])
    async def broadcast(self, message):
        for queue in list(self.clients):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(message)
    async def publish(self, kind, id):
        message = json.dumps({"type": kind, "id": id})
        try:
            if self.redis:
                await self.redis.publish("dispatchflow", message)
            else:
                await self.broadcast(message)
        except Exception:
            logging.exception("event_publish_failed")
            # Durable DB state is authoritative; clients also periodically refresh.
    async def close(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            await self.pubsub.aclose()
            await self.redis.aclose()
events = Events()
