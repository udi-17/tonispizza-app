import logging
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("telegram_bot")


HELP_TEXT = (
    "היי! אני בוט לדוגמה.\n\n"
    "/start — התחלה\n"
    "/help — עזרה\n"
    "/ping — בדיקת חיים (פינג)\n\n"
    "כל הודעת טקסט שאשלח תחזור אליך (echo)."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("היי! שמח שהצטרפת. הקלד /help לרשימת פקודות.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(HELP_TEXT)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Pong!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await update.message.reply_text(update.message.text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("פקודה לא מוכרת. הקלד /help לעזרה.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("שגיאה לא מטופלת בבוט", exc_info=context.error)


def main() -> None:
    settings = get_settings()

    application = Application.builder().token(settings.telegram_bot_token).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("ping", ping))

    # Text echo (non-commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Errors
    application.add_error_handler(error_handler)

    logger.info("Starting bot polling…")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Stopping bot — KeyboardInterrupt")
        try:
            # Give the event loop a brief moment to cleanup if needed
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
        except Exception:  # noqa: BLE001
            pass

