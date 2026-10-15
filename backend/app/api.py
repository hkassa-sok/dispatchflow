import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import session, Session as SessionFactory
from .models import Order, Driver, Merchant, Customer, Assignment
from .schemas import NewOrder, NewDriver, DriverChange, StateChange
from . import services
from .events import events
from .seed import seed

from starlette.concurrency import run_in_threadpool
router = APIRouter()

@router.get("/health")
def health(db: Session = Depends(session)):
    db.execute(select(1))
    return {"status": "ok"}

@router.get("/api/dashboard")
def dashboard(db: Session = Depends(session)):
    return {"orders": db.scalars(select(Order).order_by(Order.id.desc())).all(), "drivers": db.scalars(select(Driver)).all(), "merchants": db.scalars(select(Merchant)).all(), "customers": db.scalars(select(Customer)).all(), "assignments": db.scalars(select(Assignment).where(Assignment.active.is_(True))).all()}

@router.post("/api/orders", status_code=201)
async def new_order(data: NewOrder, db: Session = Depends(session)):
    order = services.create_order(db, data)
    await events.publish("order.created", order.id)
    return order

@router.get("/api/orders")
def orders(db: Session = Depends(session)):
    return db.scalars(select(Order).order_by(Order.id.desc())).all()

@router.get("/api/orders/{id}")
def order(id: int, db: Session = Depends(session)):
    return services.get(db, Order, id)

@router.patch("/api/orders/{id}/status")
async def status(id: int, data: StateChange, db: Session = Depends(session)):
    order = services.transition(db,id,data.status)
    await events.publish("order.status", id)
    return order

@router.post("/api/orders/{id}/dispatch", status_code=201)
async def dispatch(id: int, db: Session = Depends(session)):
    assignment = await run_in_threadpool(services.dispatch,db,id)
    await events.publish("assignment.created", id)
    return assignment

@router.post("/api/drivers", status_code=201)
async def new_driver(data: NewDriver, db: Session = Depends(session)):
    driver = Driver(**data.model_dump())
    db.add(driver)
    services.commit(db)
    await events.publish("driver.created", driver.id)
    return driver

@router.patch("/api/drivers/{id}")
async def update_driver(id: int, data: DriverChange, db: Session = Depends(session)):
    driver = services.get(db,Driver,id,True)
    if data.available and db.scalar(select(Assignment.id).where(Assignment.driver_id==id,Assignment.active.is_(True))):
        raise HTTPException(409,"Driver has an active delivery")
    for key,value in data.model_dump().items():
        setattr(driver,key,value)
    services.commit(db)
    await events.publish("driver.location",id)
    return driver

@router.post("/api/assignments/{id}/accept")
async def accept(id: int, db: Session = Depends(session)):
    snapshot = services.get(db,Assignment,id)
    services.get(db,Order,snapshot.order_id,True)
    assignment = services.get(db,Assignment,id,True)
    if not assignment.active or assignment.accepted:
        raise HTTPException(409,"Assignment is inactive or already accepted")
    assignment.accepted = True
    services.commit(db)
    await events.publish("assignment.accepted", assignment.order_id)
    return assignment

@router.post("/api/demo/step")
async def step(db: Session = Depends(session)):
    if os.getenv("DEMO_MODE","true").lower() != "true":
        raise HTTPException(404,"Demo is disabled")
    moved = 0
    for a in db.scalars(select(Assignment).where(Assignment.active.is_(True),Assignment.accepted.is_(True))).all():
        order = services.get(db,Order,a.order_id,True)
        if order.status in {"DELIVERED","CANCELLED"}:
            continue
        driver = services.get(db,Driver,a.driver_id,True)
        target = order if order.status == "PICKED_UP" else services.get(db,Merchant,order.merchant_id)
        driver.lat += (target.lat-driver.lat)*0.18
        driver.lng += (target.lng-driver.lng)*0.18
        moved += 1
    services.commit(db)
    await events.publish("simulation.tick",moved)
    return {"moved":moved}

@router.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    queue = asyncio.Queue(maxsize=100)
    events.clients.add(queue)
    async def sender():
        while True:
            try:
                message = await asyncio.wait_for(queue.get(),timeout=20)
                await ws.send_text(message)
            except asyncio.TimeoutError:
                await ws.send_json({"type":"heartbeat"})
    task = asyncio.create_task(sender())
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        events.clients.discard(queue)
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError,WebSocketDisconnect):
            pass
