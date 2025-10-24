from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from .. import services
from ..db import VALID_ROLES


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if not tg_user:
        return
    user = await asyncio.to_thread(services.get_or_create_user, tg_user.id, tg_user.username, tg_user.full_name)
    await update.effective_message.reply_text(
        "ברוך הבא לבוט המשרד!\n\n"  # Hebrew
        f"ההרשמה בוצעה. התפקיד שלך כרגע: {user.role}\n"
        "פקודות עיקריות: /help",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "פקודות זמינות:\n"
        "- /start — התחלה ורישום\n"
        "- /whoami — פרטי משתמש ותפקיד\n"
        "- /setrole @username role — רק למנהל\n"
        "- /addclient name | phone | address — הוספת לקוח\n"
        "- /listclients [query] — חיפוש לקוחות\n"
        "- /newdelivery client_id | pickup | dropoff | price | YYYY-MM-DD — יצירת משלוח\n"
        "- /assign delivery_id @courier — שיבוץ שליח\n"
        "- /status delivery_id new_status [note] — עדכון סטטוס\n"
        "- /summary [today|yesterday|YYYY-MM-DD|YYYY-MM-DD..YYYY-MM-DD] [courier:@u|client:id] — סיכום\n"
        "- /exportcsv [טווח כמו /summary] — יצוא CSV\n"
        "- /schedule_daily HH:MM [TZ] — שליחת סיכום יומי לצ'אט זה\n"
        "- /unschedule — ביטול סיכום יומי\n"
    )
    await update.effective_message.reply_text(text)


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    user = await asyncio.to_thread(services.get_or_create_user, tg_user.id, tg_user.username, tg_user.full_name)
    await update.effective_message.reply_text(
        f"אתה: @{tg_user.username or tg_user.id}\nשם: {tg_user.full_name}\nתפקיד: {user.role}"
    )


async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    user = await asyncio.to_thread(services.find_user_by_telegram_id, tg_user.id)
    if not user or user.role not in {"admin", "manager"}:
        await update.effective_message.reply_text("רק מנהלים יכולים לשנות תפקידים")
        return

    if len(context.args) < 2:
        await update.effective_message.reply_text("שימוש: /setrole @username role")
        return

    target = context.args[0]
    role = context.args[1].lower()
    if role not in VALID_ROLES:
        await update.effective_message.reply_text(f"תפקיד לא חוקי. אפשרי: {', '.join(sorted(VALID_ROLES))}")
        return

    ok, msg = await asyncio.to_thread(services.set_user_role, target, role)
    await update.effective_message.reply_text(msg)


handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_cmd),
    CommandHandler("whoami", whoami),
    CommandHandler("setrole", setrole),
]
