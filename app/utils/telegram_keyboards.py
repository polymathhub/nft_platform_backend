from typing import Dict, List, Any
def build_start_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Get Started"}],
            [{"text": "Dashboard"}, {"text": "Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Tap to begin...",
    }
def build_dashboard_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Quick Mint"}, {"text": "Send"}],
            [{"text": "Receive"}, {"text": "Wallets"}],
            [{"text": "My NFTs"}, {"text": "Marketplace"}],
            [{"text": "My Listings"}, {"text": "Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Select an action...",
    }
def build_main_menu_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Mint NFT"}, {"text": "Wallets"}],
            [{"text": "My NFTs"}, {"text": "Marketplace"}],
            [{"text": "My Listings"}, {"text": "Help"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Choose an option or type a command...",
    }
def build_wallet_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Create Wallet"}, {"text": "Import Wallet"}],
            [{"text": "List Wallets"}, {"text": "Set Primary"}],
            [{"text": "Back to Dashboard"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
def build_quick_mint_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Start Minting"}, {"text": "Send NFT"}],
            [{"text": "How to Mint"}, {"text": "Back"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
def build_blockchain_keyboard() -> Dict[str, Any]:
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
    return {
        "keyboard": [
            [{"text": "Mint NFT"}, {"text": "View My NFTs"}],
            [{"text": "Transfer"}, {"text": "Burn"}],
            [{"text": "Back to Menu"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
def build_marketplace_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Browse"}, {"text": "My Listings"}],
            [{"text": "Make Offer"}, {"text": "Cancel Listing"}],
            [{"text": "Back to Menu"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
def build_yes_no_keyboard() -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": "Yes"}, {"text": "No"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
def build_back_keyboard(label: str = "Back") -> Dict[str, Any]:
    return {
        "keyboard": [
            [{"text": label}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }
def build_custom_keyboard(buttons: List[List[str]]) -> Dict[str, Any]:
    return {
        "keyboard": buttons,
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def build_wallets_inline_keyboard(wallets: List[Dict[str, Any]]) -> Dict[str, Any]:
    buttons = []
    for wallet in wallets:
        buttons.append([{"text": wallet.get("name", "Wallet"), "callback_data": f"wallet_{wallet.get('id')}"}])
    return {
        "inline_keyboard": buttons,
    }

def build_main_actions_inline() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "Portfolio", "callback_data": "action_portfolio"}],
            [{"text": "Mint NFT", "callback_data": "action_mint"}],
            [{"text": "Marketplace", "callback_data": "action_marketplace"}],
        ],
    }

def build_dashboard_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Dashboard"}]], "resize_keyboard": True}

def build_dashboard_cta_inline() -> Dict[str, Any]:
    return {"inline_keyboard": [[{"text": "Dashboard", "callback_data": "dashboard"}]]}

def build_wallet_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Wallet"}]], "resize_keyboard": True}

def build_nft_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "NFT"}]], "resize_keyboard": True}

def build_marketplace_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Marketplace"}]], "resize_keyboard": True}

def build_blockchain_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Blockchain"}]], "resize_keyboard": True}

def build_confirmation_cta_keyboard() -> Dict[str, Any]:
    return {"inline_keyboard": [[{"text": "✓ Confirm", "callback_data": "confirm"}, {"text": "✗ Cancel", "callback_data": "cancel"}]]}

def build_balance_cta_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "View Balance"}]], "resize_keyboard": True}

def build_balance_cta_inline() -> Dict[str, Any]:
    return {"inline_keyboard": [[{"text": "View Balance", "callback_data": "balance"}]]}

def build_main_actions_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Portfolio"}, {"text": "Mint"}], [{"text": "Marketplace"}, {"text": "Settings"}]], "resize_keyboard": True}

def build_start_dashboard_inline() -> Dict[str, Any]:
    return {"inline_keyboard": [[{"text": "Open Dashboard", "callback_data": "open_dashboard", "url": "/dashboard"}]]}

def build_admin_password_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Admin Panel"}]], "resize_keyboard": True}

def build_admin_dashboard_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Users"}], [{"text": "Settings"}], [{"text": "Stats"}]], "resize_keyboard": True}

def build_commission_settings_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Set Commission"}], [{"text": "Back"}]], "resize_keyboard": True}

def build_user_management_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "View Users"}], [{"text": "Ban User"}], [{"text": "Back"}]], "resize_keyboard": True}

def build_statistics_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "View Stats"}], [{"text": "Back"}]], "resize_keyboard": True}

def build_backup_utilities_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "Backup"}], [{"text": "Restore"}], [{"text": "Back"}]], "resize_keyboard": True}

def build_blockchain_selection_keyboard() -> Dict[str, Any]:
    return {"keyboard": [[{"text": "TON"}], [{"text": "Ethereum"}], [{"text": "Solana"}], [{"text": "Back"}]], "resize_keyboard": True}
