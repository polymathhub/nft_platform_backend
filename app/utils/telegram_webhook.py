"""Telegram webhook management utilities."""

import logging
from typing import Optional
import aiohttp
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramWebhookManager:
    """Manage Telegram bot webhooks."""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.telegram_bot_token
        if not self.token:
            raise ValueError("Telegram bot token not configured")
        self.api_url = f"{self.BASE_URL}{self.token}"

    async def set_webhook(
        self,
        webhook_url: str,
        secret_token: Optional[str] = None
    ) -> bool:
        """
        Set webhook URL for Telegram bot.

        Args:
            webhook_url: Full webhook URL (e.g., https://your-app.up.railway.app/api/v1/telegram)
            secret_token: Optional secret token for verification

        Returns:
            True if successful, False otherwise
        """
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": True,
        }
        if secret_token:
            payload["secret_token"] = secret_token

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/setWebhook",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        logger.info(f"Webhook set successfully to: {webhook_url}")
                        return True
                    else:
                        error_desc = result.get("description", "Unknown error")
                        logger.error(f"Failed to set webhook: {error_desc}")
                        return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def get_webhook_info(self) -> Optional[dict]:
        """
        Get current webhook information.

        Returns:
            Webhook info dict or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/getWebhookInfo",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        return result.get("result")
                    else:
                        logger.error(f"Failed to get webhook info: {result.get('description')}")
                        return None
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return None

    async def delete_webhook(self) -> bool:
        """
        Delete current webhook (switch to polling mode).

        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/deleteWebhook",
                    json={"drop_pending_updates": True},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        logger.info("Webhook deleted successfully")
                        return True
                    else:
                        logger.error(f"Failed to delete webhook: {result.get('description')}")
                        return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    async def test_webhook(self, webhook_url: str) -> bool:
        """
        Test if webhook URL is reachable.

        Args:
            webhook_url: URL to test

        Returns:
            True if reachable, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json={"test": True},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    return response.status in [200, 400]  
        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False

async def setup_telegram_webhook():
    """
    Initialize and set Telegram webhook automatically.
    """
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured; skipping webhook setup.")
        return False

    manager = TelegramWebhookManager()
    webhook_url = "https://nftplatformbackend-production-b67d.up.railway.app/api/v1/telegram"
    success = await manager.set_webhook(webhook_url)
    if not success:
        logger.warning("Webhook setup failed, continuing startup...")
    return success
