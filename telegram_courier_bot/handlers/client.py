from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from .. import services


async def addclient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = (update.effective_message.text or "").partition(" ")[2]
    if not parts:
        await update.effective_message.reply_text("שימוש: /addclient name | phone | address")
        return
    try:
        name, phone, address = [p.strip() for p in parts.split("|") + [""] * 3][:3]
        client = await asyncio.to_thread(services.add_client, name, phone or None, address or None)
        await update.effective_message.reply_text(f"נוסף לקוח #{client.id}: {client.name}")
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאה: {e}")


async def listclients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q: Optional[str] = None
    if context.args:
        q = " ".join(context.args)
    clients = await asyncio.to_thread(services.list_clients, q)
    if not clients:
        await update.effective_message.reply_text("לא נמצאו לקוחות")
        return
    lines = [f"#{c.id} — {c.name} {('('+c.phone+')') if c.phone else ''}" for c in clients]
    await update.effective_message.reply_text("\n".join(lines))


handlers = [
    CommandHandler("addclient", addclient),
    CommandHandler("listclients", listclients),
]
