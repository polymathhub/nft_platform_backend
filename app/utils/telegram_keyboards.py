"""Telegram keyboard builders for ReplyKeyboardMarkup (CTA buttons)."""

from typing import Dict, List, Any


def build_start_keyboard() -> Dict[str, Any]:
    """Build start/welcome keyboard with main CTA."""
    return {
        "keyboard": [
            [{"text": "🚀 Get Started"}],
            [{"text": "� Dashboard"}, {"text": "❓ Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Tap to begin...",
    }


def build_dashboard_keyboard() -> Dict[str, Any]:
    """Build premium dashboard keyboard."""
    return {
        "keyboard": [
            [{"text": "⚡ Quick Mint"}, {"text": "📤 Send"}],
            [{"text": "📥 Receive"}, {"text": "👛 Wallets"}],
            [{"text": "🖼️ My NFTs"}, {"text": "🛍️ Marketplace"}],
            [{"text": "📈 My Listings"}, {"text": "❓ Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Select an action...",
    }


def build_main_menu_keyboard() -> Dict[str, Any]:
    """Build main menu keyboard with categories."""
    return {
        "keyboard": [
            [{"text": "🎨 Mint NFT"}, {"text": "👝 Wallets"}],
            [{"text": "📜 My NFTs"}, {"text": "🛍️ Marketplace"}],
            [{"text": "📊 My Listings"}, {"text": "❓ Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Choose an option or type a command...",
    }


def build_wallet_keyboard() -> Dict[str, Any]:
    """Build wallet management keyboard."""
    return {
        "keyboard": [
            [{"text": "➕ Create Wallet"}, {"text": "📥 Import Wallet"}],
            [{"text": "📋 List Wallets"}, {"text": "⭐ Set Primary"}],
            [{"text": "◀️ Back to Dashboard"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_quick_mint_keyboard() -> Dict[str, Any]:
    """Build quick mint keyboard."""
    return {
        "keyboard": [
            [{"text": "🎨 Start Minting"}, {"text": "📤 Send NFT"}],
            [{"text": "❓ How to Mint"}, {"text": "◀️ Back"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_blockchain_keyboard() -> Dict[str, Any]:
    """Build blockchain selection keyboard."""
    return {
        "keyboard": [
            [{"text": "Ethereum"}, {"text": "Polygon"}],
            [{"text": "Solana"}, {"text": "TON"}],
            [{"text": "Bitcoin"}, {"text": "◀️ Cancel"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def build_nft_operations_keyboard() -> Dict[str, Any]:
    """Build NFT operations keyboard."""
    return {
        "keyboard": [
            [{"text": "🎨 Mint NFT"}, {"text": "📜 View My NFTs"}],
            [{"text": "📤 Transfer"}, {"text": "🔥 Burn"}],
            [{"text": "◀️ Back to Menu"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_marketplace_keyboard() -> Dict[str, Any]:
    """Build marketplace keyboard."""
    return {
        "keyboard": [
            [{"text": "🔍 Browse"}, {"text": "📊 My Listings"}],
            [{"text": "💬 Make Offer"}, {"text": "❌ Cancel Listing"}],
            [{"text": "◀️ Back to Menu"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_yes_no_keyboard() -> Dict[str, Any]:
    """Build simple yes/no keyboard."""
    return {
        "keyboard": [
            [{"text": "✅ Yes"}, {"text": "❌ No"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def build_back_keyboard(label: str = "◀️ Back") -> Dict[str, Any]:
    """Build simple back button keyboard."""
    return {
        "keyboard": [
            [{"text": label}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def build_custom_keyboard(buttons: List[List[str]]) -> Dict[str, Any]:
    """Build custom keyboard from button list.
    
    Args:
        buttons: 2D list of button labels, e.g. [["Button1", "Button2"], ["Button3"]]
    
    Returns:
        ReplyKeyboardMarkup dict
    """
    keyboard = [[{"text": btn} for btn in row] for row in buttons]
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def remove_keyboard() -> Dict[str, Any]:
    """Build keyboard removal (hide keyboard)."""
    return {
        "remove_keyboard": True,
    }
