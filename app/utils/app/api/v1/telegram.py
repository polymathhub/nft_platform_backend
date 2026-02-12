from fastapi import APIRouter, Request
import logging

from app.services.telegram_bot_service import TelegramBotService

router = APIRouter()

logger = logging.getLogger(__name__)

bot = TelegramBotService()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint.
    Receives updates from Telegram.
    """

    update = await request.json()

    logger.info(f"Telegram update received: {update}")

    message = update.get("message")

    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")


    if text.startswith("/start"):
        await bot.send_start_message(chat_id, message["from"].get("username", "User"))

    elif text.startswith("/help"):
        await bot.send_start_message(chat_id, message["from"].get("username", "User"))

    else:
        await bot.send_message(
            chat_id,
            "🤖 Command not recognized.\nUse /start to see available commands."
        )

    return {"ok": True}
