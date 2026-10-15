from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from .models import Order, Driver, Merchant, Customer, Assignment
from .dispatch import rank, Candidate

TRANSITIONS = {
    "CREATED": {"ACCEPTED", "CANCELLED"}, "ACCEPTED": {"PREPARING", "CANCELLED"},
    "PREPARING": {"READY_FOR_PICKUP", "CANCELLED"}, "READY_FOR_PICKUP": {"PICKED_UP", "CANCELLED"},
    "PICKED_UP": {"DELIVERED"}, "DELIVERED": set(), "CANCELLED": set(),
}
def get(db, model, id, lock=False):
    q = select(model).where(model.id == id)
    obj = db.scalar(q.with_for_update() if lock else q)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj

def commit(db):
    try:
        db.commit()
    except (IntegrityError, OperationalError):
        db.rollback()
        raise HTTPException(409, "Concurrent change conflicts with this request; retry")

def active(db, order_id):
    return db.scalar(select(Assignment).where(Assignment.order_id == order_id, Assignment.active.is_(True)))

def create_order(db, data):
    get(db, Customer, data.customer_id)
    get(db, Merchant, data.merchant_id)
    order = Order(**data.model_dump())
    db.add(order)
    commit(db)
    return order

def dispatch(db, id):
    order = get(db, Order, id, True)
    if order.status not in {"ACCEPTED", "PREPARING", "READY_FOR_PICKUP"} or active(db, id):
        raise HTTPException(409, "Order is not dispatchable or already assigned")
    merchant = get(db, Merchant, order.merchant_id)
    drivers = db.scalars(select(Driver).where(Driver.available.is_(True))).all()
    for score, driver_id in rank([Candidate(d.id,d.lat,d.lng) for d in drivers], (merchant.lat,merchant.lng), order.prep_minutes):
        # Lock candidate, re-read after waiting; skip busy rows on PostgreSQL.
        driver = db.scalar(select(Driver).where(Driver.id == driver_id, Driver.available.is_(True)).with_for_update(skip_locked=True).execution_options(populate_existing=True))
        if driver is None:
            continue
        driver.available = False
        assignment = Assignment(order_id=id, driver_id=driver_id, score=score)
        db.add(assignment)
        commit(db)
        return assignment
    raise HTTPException(409, "No available driver")

def transition(db, id, status):
    order = get(db, Order, id, True)
    if status not in TRANSITIONS[order.status]:
        raise HTTPException(409, f"Invalid transition: {order.status} → {status}")
    assignment = active(db, id)
    if status in {"PICKED_UP", "DELIVERED"} and (not assignment or not assignment.accepted):
        raise HTTPException(409, "An accepted assignment is required")
    order.status = status
    if status in {"CANCELLED", "DELIVERED"} and assignment:
        get(db, Driver, assignment.driver_id, True).available = True
        assignment.active = False
    commit(db)
    return order
