from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import ApplicationBuilder

from .config import load_config
from .db import init_db
from .handlers.common import handlers as common_handlers
from .handlers.client import handlers as client_handlers
from .handlers.delivery import handlers as delivery_handlers
from .handlers.summary import handlers as summary_handlers, daily_summary_job
from . import services


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("courier-bot")


async def setup_jobs(application):
    # Load schedules and register jobs
    schedules = await asyncio.to_thread(services.get_all_schedules)
    for sched in schedules:
        try:
            hour, minute = map(int, sched.time_of_day.split(":"))
            tz = ZoneInfo(sched.timezone)
            job_name = f"daily_{sched.chat_id}"
            for job in application.job_queue.get_jobs_by_name(job_name):
                job.schedule_removal()
            application.job_queue.run_daily(
                callback=daily_summary_job,
                time=datetime.time(hour, minute, tzinfo=tz),
                name=job_name,
                data={"chat_id": sched.chat_id, "timezone": sched.timezone},
            )
            logger.info("Scheduled daily summary for chat %s at %s %s", sched.chat_id, sched.time_of_day, sched.timezone)
        except Exception as e:
            logger.exception("Failed to schedule job for chat %s: %s", sched.chat_id, e)


async def main() -> None:
    cfg = load_config()

    # Ensure data/exports directories
    Path("/workspace/data").mkdir(parents=True, exist_ok=True)
    Path("/workspace/exports").mkdir(parents=True, exist_ok=True)

    # Init DB
    init_db(cfg.database_url)

    app = ApplicationBuilder().token(cfg.bot_token).build()
    app.bot_data["timezone"] = cfg.timezone

    # Register handlers
    for h in common_handlers + client_handlers + delivery_handlers + summary_handlers:
        app.add_handler(h)

    await setup_jobs(app)

    logger.info("Bot starting...")
    await app.initialize()
    await app.start()
    # Run until Ctrl+C
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    asyncio.run(main())
