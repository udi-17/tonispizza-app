from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from .. import services
from ..db import VALID_STATUSES


def _parse_decimal(value: str) -> Optional[Decimal]:
    try:
        v = value.strip()
        if not v:
            return None
        return Decimal(v)
    except InvalidOperation:
        return None


def _parse_date(value: str) -> Optional[date]:
    v = value.strip()
    if not v:
        return None
    try:
        return date.fromisoformat(v)
    except Exception:
        return None


async def newdelivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = (update.effective_message.text or "").partition(" ")[2]
    if not parts:
        await update.effective_message.reply_text("שימוש: /newdelivery client_id | pickup | dropoff | price | YYYY-MM-DD")
        return
    try:
        tokens = [p.strip() for p in parts.split("|") + [""] * 5][:5]
        client_id = int(tokens[0])
        pickup = tokens[1]
        dropoff = tokens[2]
        price = _parse_decimal(tokens[3])
        due = _parse_date(tokens[4])
        d = await asyncio.to_thread(services.create_delivery, client_id, pickup, dropoff, price, due)
        await update.effective_message.reply_text(f"נוצר משלוח #{d.id} ללקוח #{d.client_id}")
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאה: {e}")


async def assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_message.reply_text("שימוש: /assign delivery_id @courier")
        return
    try:
        delivery_id = int(context.args[0])
        courier_tag = context.args[1]
        if not courier_tag.startswith("@"):
            await update.effective_message.reply_text("יש להשתמש ב-@username של השליח")
            return
        courier = await asyncio.to_thread(services.find_user_by_username, courier_tag[1:])
        if not courier:
            await update.effective_message.reply_text("לא נמצא שליח. ודא ש-@username נכון ושעשה /start")
            return
        actor = await asyncio.to_thread(services.find_user_by_telegram_id, update.effective_user.id)
        d = await asyncio.to_thread(services.assign_courier, delivery_id, courier.id, actor.id if actor else None)
        await update.effective_message.reply_text(f"משלוח #{d.id} שובץ ל-@{courier.username}")
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאה: {e}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_message.reply_text("שימוש: /status delivery_id new_status [note]")
        return
    try:
        delivery_id = int(context.args[0])
        new_status = context.args[1].lower()
        if new_status not in VALID_STATUSES:
            await update.effective_message.reply_text(f"סטטוס לא חוקי. אפשרי: {', '.join(sorted(VALID_STATUSES))}")
            return
        note = " ".join(context.args[2:]) if len(context.args) > 2 else None
        actor = await asyncio.to_thread(services.find_user_by_telegram_id, update.effective_user.id)
        d = await asyncio.to_thread(services.update_delivery_status, delivery_id, new_status, actor.id if actor else None, note)
        await update.effective_message.reply_text(f"עודכן סטטוס משלוח #{d.id} ל-{new_status}")
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאה: {e}")


handlers = [
    CommandHandler("newdelivery", newdelivery),
    CommandHandler("assign", assign),
    CommandHandler("status", status),
]
