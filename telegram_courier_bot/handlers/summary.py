from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Optional, Tuple

from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from .. import services


def _parse_range(arg: Optional[str]) -> Tuple[date, date]:
    today = date.today()
    if not arg or arg.lower() == "today":
        return today, today
    if arg.lower() == "yesterday":
        y = today - timedelta(days=1)
        return y, y
    if ".." in arg:
        s, e = arg.split("..", 1)
        return date.fromisoformat(s), date.fromisoformat(e)
    # single date
    return date.fromisoformat(arg), date.fromisoformat(arg)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /summary [range] [courier:@user|client:id]
    range_arg = None
    courier_username = None
    client_id = None

    for a in context.args:
        if a.startswith("courier:"):
            courier_username = a.split(":", 1)[1].lstrip("@")
        elif a.startswith("client:"):
            try:
                client_id = int(a.split(":", 1)[1])
            except ValueError:
                client_id = None
        else:
            range_arg = a

    try:
        start, end = _parse_range(range_arg)
    except Exception:
        await update.effective_message.reply_text("טווח לא חוקי. נסה: today | yesterday | YYYY-MM-DD | YYYY-MM-DD..YYYY-MM-DD")
        return

    data = await asyncio.to_thread(services.summarize, start, end, courier_username, client_id)

    lines = [
        f"סיכום {start.isoformat()} עד {end.isoformat()}",
        f"סה""כ משלוחים: {data['total']}",
        f"נמסרו: {data['delivered']}",
        f"בתהליך: {data['in_progress']}",
        f"בוטלו: {data['canceled']}",
        f"סך הכל כספי: {data['amount_total']:.2f}",
    ]
    if data.get("by_courier"):
        lines.append("\nלפי שליח:")
        for name, count in sorted(data["by_courier"].items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {name}: {count}")

    await update.effective_message.reply_text("\n".join(lines))


async def exportcsv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    range_arg = None
    courier_username = None
    client_id = None

    for a in context.args:
        if a.startswith("courier:"):
            courier_username = a.split(":", 1)[1].lstrip("@")
        elif a.startswith("client:"):
            try:
                client_id = int(a.split(":", 1)[1])
            except ValueError:
                client_id = None
        else:
            range_arg = a

    try:
        start, end = _parse_range(range_arg)
    except Exception:
        await update.effective_message.reply_text("טווח לא חוקי. נסה: today | yesterday | YYYY-MM-DD | YYYY-MM-DD..YYYY-MM-DD")
        return

    out_dir = Path("/workspace/exports")
    path = await asyncio.to_thread(services.export_deliveries_csv, start, end, out_dir, courier_username, client_id)
    await update.effective_message.reply_document(document=path.open("rb"), filename=path.name, caption=f"CSV {start}..{end}")


async def schedule_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text("שימוש: /schedule_daily HH:MM [Timezone, לדוגמה Asia/Jerusalem]")
        return
    hhmm = context.args[0]
    tz = context.args[1] if len(context.args) > 1 else context.bot_data.get("timezone", "UTC")

    try:
        sched = await asyncio.to_thread(services.set_daily_schedule, update.effective_chat.id, hhmm, tz)
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאה: {e}")
        return

    # Register on job queue now
    try:
        hour, minute = map(int, sched.time_of_day.split(":"))
        tzinfo = ZoneInfo(sched.timezone)
        application = context.application
        job_name = f"daily_{sched.chat_id}"
        # Remove existing job if exists
        for job in application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        application.job_queue.run_daily(
            callback=daily_summary_job,
            time=time(hour, minute, tzinfo=tzinfo),
            name=job_name,
            data={"chat_id": sched.chat_id, "timezone": sched.timezone},
        )
        await update.effective_message.reply_text(f"תוזמן סיכום יומי ב-{sched.time_of_day} ({sched.timezone})")
    except Exception as e:
        await update.effective_message.reply_text(f"שגיאת תזמון: {e}")


async def unschedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ok = await asyncio.to_thread(services.clear_schedule, update.effective_chat.id)
    job_name = f"daily_{update.effective_chat.id}"
    for job in context.application.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    await update.effective_message.reply_text("התזמון בוטל" if ok else "לא נמצא תזמון פעיל")


async def daily_summary_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data or {}
    chat_id = data.get("chat_id")
    tzname = data.get("timezone", "UTC")
    tz = ZoneInfo(tzname)
    now = datetime.now(tz)
    # By default: send summary for yesterday
    y = (now - timedelta(days=1)).date()
    summary_data = await asyncio.to_thread(services.summarize, y, y, None, None)
    lines = [
        f"סיכום יומי עבור {y.isoformat()}",
        f"סה""כ משלוחים: {summary_data['total']}",
        f"נמסרו: {summary_data['delivered']}",
        f"בתהליך: {summary_data['in_progress']}",
        f"בוטלו: {summary_data['canceled']}",
        f"סך הכל כספי: {summary_data['amount_total']:.2f}",
    ]
    if summary_data.get("by_courier"):
        lines.append("\nלפי שליח:")
        for name, count in sorted(summary_data["by_courier"].items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- {name}: {count}")
    try:
        await context.bot.send_message(chat_id=chat_id, text="\n".join(lines))
    except Exception:
        pass


handlers = [
    CommandHandler("summary", summary),
    CommandHandler("exportcsv", exportcsv),
    CommandHandler("schedule_daily", schedule_daily),
    CommandHandler("unschedule", unschedule),
]
