from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, Boolean, DateTime, Index, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class Merchant(Base):
    __tablename__ = "merchants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)

class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (CheckConstraint("lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("status IN ('CREATED','ACCEPTED','PREPARING','READY_FOR_PICKUP','PICKED_UP','DELIVERED','CANCELLED')"), CheckConstraint("prep_minutes >= 0"), CheckConstraint("lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180"))
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="CREATED", index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    prep_minutes: Mapped[float] = mapped_column(Float, default=8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float)
    __table_args__ = (
        Index("uq_active_driver", "driver_id", unique=True, postgresql_where=text("active = true"), sqlite_where=text("active = 1")),
        Index("uq_active_order", "order_id", unique=True, postgresql_where=text("active = true"), sqlite_where=text("active = 1")),
    )
