from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from .db import Client, Delivery, Schedule, SessionLocal, StatusHistory, User, VALID_ROLES, VALID_STATUSES


# ---------- Users and roles ----------

def get_or_create_user(telegram_id: int, username: Optional[str], full_name: Optional[str]) -> User:
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id, username=username, full_name=full_name, role="viewer")
            session.add(user)
            session.commit()
        else:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if updated:
                session.commit()
        return user


def set_user_role(target_identifier: str, role: str) -> Tuple[bool, str]:
    role = role.lower()
    if role not in VALID_ROLES:
        return False, f"Invalid role: {role}. Valid: {', '.join(sorted(VALID_ROLES))}"

    with SessionLocal() as session:
        user: Optional[User] = None
        if target_identifier.startswith("@"):
            username = target_identifier[1:].lower()
            user = session.execute(select(User).where(func.lower(User.username) == username)).scalar_one_or_none()
        elif target_identifier.isdigit():
            user = session.execute(select(User).where(User.telegram_id == int(target_identifier))).scalar_one_or_none()
        else:
            return False, "Use @username or telegram numeric id"

        if user is None:
            return False, "User not found in DB. Ask them to /start first."

        user.role = role
        session.commit()
        return True, f"Updated role for {user.username or user.telegram_id} to {role}"


# ---------- Clients ----------

def add_client(name: str, phone: Optional[str], address: Optional[str]) -> Client:
    with SessionLocal() as session:
        client = Client(name=name.strip(), phone=(phone or "").strip() or None, address=(address or "").strip() or None)
        session.add(client)
        session.commit()
        session.refresh(client)
        return client


def list_clients(q: Optional[str] = None, limit: int = 50) -> List[Client]:
    with SessionLocal() as session:
        stmt = select(Client).order_by(Client.id.desc()).limit(limit)
        if q:
            like = f"%{q.lower()}%"
            stmt = select(Client).where(func.lower(Client.name).like(like)).order_by(Client.id.desc()).limit(limit)
        return list(session.execute(stmt).scalars())


# ---------- Deliveries ----------

def create_delivery(
    client_id: int,
    pickup_address: str,
    dropoff_address: str,
    price: Optional[Decimal],
    due: Optional[date],
    description: Optional[str] = None,
) -> Delivery:
    with SessionLocal() as session:
        client = session.get(Client, client_id)
        if not client:
            raise ValueError("Client not found")

        delivery = Delivery(
            client_id=client_id,
            pickup_address=pickup_address.strip(),
            dropoff_address=dropoff_address.strip(),
            price=price,
            due_date=due,
            description=(description or None),
            status="created",
            created_at=datetime.utcnow(),
            last_update_at=datetime.utcnow(),
        )
        session.add(delivery)
        session.flush()
        session.add(StatusHistory(delivery_id=delivery.id, status="created", note="created", created_at=datetime.utcnow()))
        session.commit()
        session.refresh(delivery)
        return delivery


def assign_courier(delivery_id: int, courier_user_id: int, actor_user_id: Optional[int]) -> Delivery:
    with SessionLocal() as session:
        delivery = session.get(Delivery, delivery_id)
        if not delivery:
            raise ValueError("Delivery not found")

        courier = session.get(User, courier_user_id)
        if not courier or courier.role != "courier":
            raise ValueError("Target user is not a courier")

        delivery.courier_user_id = courier_user_id
        delivery.status = "assigned"
        delivery.last_update_at = datetime.utcnow()
        session.add(StatusHistory(
            delivery_id=delivery.id,
            status="assigned",
            note=f"assigned to {courier.username or courier.telegram_id}",
            changed_by_user_id=actor_user_id,
            created_at=datetime.utcnow(),
        ))
        session.commit()
        session.refresh(delivery)
        return delivery


def update_delivery_status(delivery_id: int, new_status: str, actor_user_id: Optional[int], note: Optional[str] = None) -> Delivery:
    new_status = new_status.lower().strip()
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    with SessionLocal() as session:
        delivery = session.get(Delivery, delivery_id)
        if not delivery:
            raise ValueError("Delivery not found")

        delivery.status = new_status
        now = datetime.utcnow()
        delivery.last_update_at = now
        if new_status == "delivered":
            delivery.delivered_at = now
        session.add(StatusHistory(
            delivery_id=delivery.id,
            status=new_status,
            note=note,
            changed_by_user_id=actor_user_id,
            created_at=now,
        ))
        session.commit()
        session.refresh(delivery)
        return delivery


# ---------- Summaries & exports ----------

def _date_range_stmt(start: date, end: date):
    # Inclusive end-of-day filter
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return start_dt, end_dt


def summarize(start: date, end: date, courier_username: Optional[str] = None, client_id: Optional[int] = None) -> Dict[str, Any]:
    start_dt, end_dt = _date_range_stmt(start, end)
    with SessionLocal() as session:
        conditions = [Delivery.created_at >= start_dt, Delivery.created_at <= end_dt]

        if courier_username:
            courier = session.execute(select(User).where(func.lower(User.username) == courier_username.lower())).scalar_one_or_none()
            if not courier:
                return {"total": 0, "delivered": 0, "in_progress": 0, "canceled": 0, "amount_total": 0.0, "courier": courier_username}
            conditions.append(Delivery.courier_user_id == courier.id)

        if client_id:
            conditions.append(Delivery.client_id == client_id)

        q = select(Delivery).where(and_(*conditions))
        deliveries = list(session.execute(q).scalars())

        total = len(deliveries)
        delivered = sum(1 for d in deliveries if d.status == "delivered")
        canceled = sum(1 for d in deliveries if d.status == "canceled")
        in_progress = total - delivered - canceled
        amount_total = float(sum((d.price or Decimal(0)) for d in deliveries))

        by_courier: Dict[str, int] = {}
        for d in deliveries:
            key = (d.courier.username if d.courier and d.courier.username else str(d.courier.telegram_id) if d.courier else "unassigned")
            by_courier[key] = by_courier.get(key, 0) + 1

        return {
            "total": total,
            "delivered": delivered,
            "in_progress": in_progress,
            "canceled": canceled,
            "amount_total": amount_total,
            "by_courier": by_courier,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }


def export_deliveries_csv(start: date, end: date, out_dir: Path, courier_username: Optional[str] = None, client_id: Optional[int] = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    start_dt, end_dt = _date_range_stmt(start, end)
    with SessionLocal() as session:
        conditions = [Delivery.created_at >= start_dt, Delivery.created_at <= end_dt]
        if courier_username:
            courier = session.execute(select(User).where(func.lower(User.username) == courier_username.lower())).scalar_one_or_none()
            if courier:
                conditions.append(Delivery.courier_user_id == courier.id)
            else:
                conditions.append(Delivery.courier_user_id == -1)  # no results
        if client_id:
            conditions.append(Delivery.client_id == client_id)

        q = select(Delivery).where(and_(*conditions)).order_by(Delivery.id.desc())
        deliveries = list(session.execute(q).scalars())

        filename = f"deliveries_{start.isoformat()}_{end.isoformat()}.csv"
        path = out_dir / filename
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "id", "created_at", "client", "pickup", "dropoff", "price", "status", "courier", "delivered_at", "due_date", "description",
            ])
            for d in deliveries:
                w.writerow([
                    d.id,
                    d.created_at.isoformat(sep=" ", timespec="seconds"),
                    (d.client.name if d.client else d.client_id),
                    d.pickup_address,
                    d.dropoff_address,
                    float(d.price) if d.price is not None else "",
                    d.status,
                    (d.courier.username if d.courier and d.courier.username else d.courier.telegram_id if d.courier else ""),
                    d.delivered_at.isoformat(sep=" ", timespec="seconds") if d.delivered_at else "",
                    d.due_date.isoformat() if d.due_date else "",
                    d.description or "",
                ])
        return path


# ---------- Schedules ----------

def get_all_schedules() -> List[Schedule]:
    with SessionLocal() as session:
        return list(session.execute(select(Schedule).where(Schedule.active == True)).scalars())  # noqa: E712


def set_daily_schedule(chat_id: int, time_hhmm: str, timezone: str, scope: str = "daily") -> Schedule:
    hhmm = time_hhmm.strip()
    if len(hhmm) != 5 or hhmm[2] != ":":
        raise ValueError("Time must be HH:MM (24h)")

    with SessionLocal() as session:
        existing = session.execute(select(Schedule).where(Schedule.chat_id == chat_id, Schedule.scope == scope)).scalar_one_or_none()
        if existing:
            existing.time_of_day = hhmm
            existing.timezone = timezone
            existing.active = True
            session.commit()
            session.refresh(existing)
            return existing
        sched = Schedule(chat_id=chat_id, time_of_day=hhmm, timezone=timezone, active=True, scope=scope)
        session.add(sched)
        session.commit()
        session.refresh(sched)
        return sched


def clear_schedule(chat_id: int, scope: str = "daily") -> bool:
    with SessionLocal() as session:
        sched = session.execute(select(Schedule).where(Schedule.chat_id == chat_id, Schedule.scope == scope)).scalar_one_or_none()
        if not sched:
            return False
        sched.active = False
        session.commit()
        return True


# ---------- Helpers ----------

def find_user_by_username(username: str) -> Optional[User]:
    with SessionLocal() as session:
        return session.execute(select(User).where(func.lower(User.username) == username.lower())).scalar_one_or_none()


def find_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    with SessionLocal() as session:
        return session.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
