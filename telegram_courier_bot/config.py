from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class AppConfig:
    bot_token: str
    database_url: str
    timezone: str = "UTC"
    admin_chat_id: Optional[int] = None


def load_config() -> AppConfig:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set. Put it in .env or environment.")

    database_url = os.getenv("DB_URL", "sqlite:////workspace/data/courier_bot.db").strip()

    timezone = os.getenv("TIMEZONE", "UTC").strip() or "UTC"

    admin_chat_id_env = os.getenv("ADMIN_CHAT_ID", "").strip()
    admin_chat_id = int(admin_chat_id_env) if admin_chat_id_env.isdigit() else None

    return AppConfig(
        bot_token=bot_token,
        database_url=database_url,
        timezone=timezone,
        admin_chat_id=admin_chat_id,
    )
