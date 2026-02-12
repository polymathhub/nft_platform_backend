"""Telegram utilities for bot integration."""

import logging
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class TelegramCommand(str, Enum):
    START = "/start"
    HELP = "/help"
    WALLET = "/wallet"
    MINT = "/mint"
    STATUS = "/status"
    CANCEL = "/cancel"


class TelegramCommandParser:
    @staticmethod
    def parse_command(message: str) -> tuple[Optional[str], List[str]]:
        parts = message.strip().split(maxsplit=1)
        if not parts:
            return None, []
        command = parts[0] if parts[0].startswith("/") else None
        args = parts[1].split() if len(parts) > 1 else []
        return command, args

    @staticmethod
    def parse_mint_command(args: List[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if len(args) < 2:
            return None, None, None
        wallet_id = args[0]
        nft_name = args[1]
        description = " ".join(args[2:]) if len(args) > 2 else None
        return wallet_id, nft_name, description

    @staticmethod
    def parse_status_command(args: List[str]) -> Optional[str]:
        return args[0] if args else None


from app.ui.designer import (
    bold,
    code,
    italic,
    link,
    truncate_address,
    create_wallet_message,
    create_nft_message,
    create_wallet_buttons as build_wallet_selector,
)


class TelegramMarkup:
    @staticmethod
    def create_wallet_buttons(wallets: List[Any]) -> dict:
        # Delegate to shared UI builder
        return build_wallet_selector(wallets)

    @staticmethod
    def create_confirm_buttons() -> dict:
        return {
            "inline_keyboard": [
                [
                    {"text": "✅ Confirm", "callback_data": "confirm"},
                    {"text": "❌ Cancel", "callback_data": "cancel"},
                ]
            ]
        }

    @staticmethod
    def create_main_menu() -> dict:
        return {
            "keyboard": [
                [{"text": "💼 My Wallets"}],
                [{"text": "🎨 Mint NFT"}],
                [{"text": "📊 View NFTs"}],
                [{"text": "ℹ️ Help"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }


class TelegramValidation:
    """Validation helpers for Telegram input."""

    @staticmethod
    def is_valid_uuid(value: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            from uuid import UUID
            UUID(value)
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def is_valid_nft_name(name: str) -> bool:
        """Validate NFT name."""
        return 1 <= len(name) <= 255

    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Validate NFT description."""
        return len(description) <= 2000

    @staticmethod
    def is_valid_image_url(url: str) -> bool:
        """Validate image URL."""
        if not url:
            return True  # Optional
        return url.startswith(("http://", "https://")) and len(url) <= 500

    @staticmethod
    def validate_mint_input(wallet_id: str, nft_name: str, description: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Validate mint command input."""
        if not TelegramValidation.is_valid_uuid(wallet_id):
            return False, "Invalid wallet ID format"
        
        if not TelegramValidation.is_valid_nft_name(nft_name):
            return False, "NFT name must be 1-255 characters"
        
        if description and not TelegramValidation.is_valid_description(description):
            return False, "Description must be less than 2000 characters"
        
        return True, None


# Type hint for wallet and NFT objects
Any = object
