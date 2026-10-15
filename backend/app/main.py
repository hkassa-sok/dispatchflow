import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import session, Session as SessionFactory
from .models import Order, Driver, Merchant, Customer, Assignment
from .schemas import NewOrder, NewDriver, DriverChange, StateChange
from . import services
from .events import events
from .seed import seed

import json
class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {"timestamp": self.formatTime(record), "level": record.levelname, "message": record.getMessage()}
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger("dispatchflow")
@asynccontextmanager
async def lifespan(app):
    await events.start()
    if os.getenv("DEMO_MODE", "true").lower() == "true":
        with SessionFactory() as db:
            seed(db)
    yield
    await events.close()
app = FastAPI(title="DispatchFlow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173,http://localhost:8080").split(","), allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_request(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    request_id = uuid.uuid4().hex
    response.headers["X-Request-ID"] = request_id
    logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%.2f", request_id, request.method, request.url.path, response.status_code, (time.perf_counter()-start)*1000)
    return response

from .api import router
app.include_router(router)
