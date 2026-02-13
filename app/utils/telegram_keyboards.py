"""Telegram keyboard builders for ReplyKeyboardMarkup (CTA buttons) and InlineKeyboardMarkup.

This module provides two types of Telegram keyboards:

1. ReplyKeyboardMarkup (Traditional):
   - Buttons appear below the message input field
   - User presses button and it sends the button text as a message
   - Persists between messages
   - Better for general navigation

2. InlineKeyboardMarkup (Inline - NEW):
   - Buttons appear directly attached to the message
   - Uses callback_data instead of text messages
   - Buttons trigger callback_query updates (no spam messages)
   - Buttons disappear after use (unless preserved)
   - Better for specific message actions (confirm, select, etc.)

For interactive dashboards and action menus, prefer inline keyboards!
"""

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
            [{"text": "📥 Receive"}, {"text": "👝 Wallets"}],
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


# ============== INLINE KEYBOARDS (with callback_data) ==============


def build_dashboard_inline_keyboard() -> Dict[str, Any]:
    """Build inline keyboard for dashboard with action buttons."""
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ Quick Mint", "callback_data": "action:quick_mint"},
                {"text": "📤 Send NFT", "callback_data": "action:transfer"},
            ],
            [
                {"text": "📥 Receive", "callback_data": "action:receive"},
                {"text": "👝 Wallets", "callback_data": "action:wallets"},
            ],
            [
                {"text": "🖼️ My NFTs", "callback_data": "action:mynfts"},
                {"text": "🛍️ Marketplace", "callback_data": "action:browse"},
            ],
            [
                {"text": "📈 My Listings", "callback_data": "action:mylistings"},
                {"text": "❓ Help", "callback_data": "action:help"},
            ],
        ]
    }


def build_wallet_inline_keyboard() -> Dict[str, Any]:
    """Build inline keyboard for wallet management."""
    return {
        "inline_keyboard": [
            [
                {"text": "➕ Create New", "callback_data": "wallet:create"},
                {"text": "📥 Import", "callback_data": "wallet:import"},
            ],
            [
                {"text": "📋 List All", "callback_data": "wallet:list"},
                {"text": "⭐ Set Primary", "callback_data": "wallet:set_primary"},
            ],
            [
                {"text": "◀️ Back", "callback_data": "action:dashboard"},
            ],
        ]
    }


def build_nft_inline_keyboard() -> Dict[str, Any]:
    """Build inline keyboard for NFT actions."""
    return {
        "inline_keyboard": [
            [
                {"text": "🎨 Mint NFT", "callback_data": "nft:mint"},
                {"text": "📜 View My NFTs", "callback_data": "nft:list"},
            ],
            [
                {"text": "📤 Transfer", "callback_data": "nft:transfer"},
                {"text": "🔥 Burn", "callback_data": "nft:burn"},
            ],
            [
                {"text": "🛍️ List for Sale", "callback_data": "nft:list_sale"},
                {"text": "◀️ Back", "callback_data": "action:dashboard"},
            ],
        ]
    }


def build_marketplace_inline_keyboard() -> Dict[str, Any]:
    """Build inline keyboard for marketplace."""
    return {
        "inline_keyboard": [
            [
                {"text": "🔍 Browse", "callback_data": "market:browse"},
                {"text": "❤️ Favorites", "callback_data": "market:favorites"},
            ],
            [
                {"text": "💬 Make Offer", "callback_data": "market:offer"},
                {"text": "📊 My Listings", "callback_data": "market:mylistings"},
            ],
            [
                {"text": "◀️ Back", "callback_data": "action:dashboard"},
            ],
        ]
    }


def build_confirmation_inline_keyboard(action_id: str = "") -> Dict[str, Any]:
    """Build yes/no confirmation inline keyboard."""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Confirm", "callback_data": f"confirm:yes:{action_id}"},
                {"text": "❌ Cancel", "callback_data": f"confirm:no:{action_id}"},
            ],
        ]
    }


def build_blockchain_inline_keyboard() -> Dict[str, Any]:
    """Build inline keyboard for blockchain selection."""
    return {
        "inline_keyboard": [
            [
                {"text": "⟡ Ethereum", "callback_data": "blockchain:ethereum"},
                {"text": "🔶 Polygon", "callback_data": "blockchain:polygon"},
            ],
            [
                {"text": "◎ Solana", "callback_data": "blockchain:solana"},
                {"text": "💎 TON", "callback_data": "blockchain:ton"},
            ],
            [
                {"text": "₿ Bitcoin", "callback_data": "blockchain:bitcoin"},
                {"text": "❌ Cancel", "callback_data": "action:cancel"},
            ],
        ]
    }


def build_custom_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Build custom inline keyboard from button list.
    
    Args:
        buttons: 2D list of button dicts with 'text' and 'callback_data' keys
                Example: [[{"text": "Button1", "callback_data": "action:1"}]]
    
    Returns:
        InlineKeyboardMarkup dict
    """
    return {
        "inline_keyboard": buttons
    }


def build_url_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Build inline keyboard with URL buttons.
    
    Args:
        buttons: 2D list of button dicts with 'text' and 'url' keys
                Example: [[{"text": "Visit", "url": "https://example.com"}]]
    
    Returns:
        InlineKeyboardMarkup dict with URL buttons
    """
    return {
        "inline_keyboard": buttons
    }
