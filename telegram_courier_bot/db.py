from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


VALID_ROLES = {"admin", "manager", "courier", "viewer"}
VALID_STATUSES = {"created", "assigned", "picked_up", "in_transit", "delivered", "canceled", "failed"}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="viewer")
    phone = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    deliveries = relationship("Delivery", back_populates="courier", foreign_keys="Delivery.courier_user_id")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    deliveries = relationship("Delivery", back_populates="client")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True)

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    client = relationship("Client", back_populates="deliveries")

    pickup_address = Column(Text, nullable=False)
    dropoff_address = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    price = Column(Numeric(10, 2), nullable=True)
    status = Column(String(32), nullable=False, default="created", index=True)

    courier_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    courier = relationship("User", back_populates="deliveries", foreign_keys=[courier_user_id])

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    due_date = Column(Date, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    last_update_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    history = relationship("StatusHistory", back_populates="delivery", cascade="all, delete-orphan")


Index("ix_deliveries_status_courier", Delivery.status, Delivery.courier_user_id)


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    note = Column(Text, nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    delivery = relationship("Delivery", back_populates="history")
    changed_by_user = relationship("User")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    time_of_day = Column(String(8), nullable=False)  # HH:MM (24h)
    timezone = Column(String(64), nullable=False, default="UTC")
    active = Column(Boolean, nullable=False, default=True)
    scope = Column(String(32), nullable=False, default="daily")  # future-proofing
    filters = Column(Text, nullable=True)  # JSON string (optional)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


_engine = None
SessionLocal: sessionmaker


def init_engine(database_url: str):
    global _engine, SessionLocal
    _engine = create_engine(database_url, future=True, echo=False)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False)


def init_db(database_url: str):
    init_engine(database_url)
    Base.metadata.create_all(_engine)
