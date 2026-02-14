from typing import Optional, List, Dict, Any
import html


def _escape_html(text: Optional[str]) -> str:
    if text is None:
        return ""
    return html.escape(str(text))


# --- Formatting helpers (shared across telegram UI) ---
def bold(text: Optional[str]) -> str:
    return f"<b>{_escape_html(text)}</b>"


def code(text: Optional[str]) -> str:
    return f"<code>{_escape_html(text)}</code>"


def italic(text: Optional[str]) -> str:
    return f"<i>{_escape_html(text)}</i>"


def link(text: Optional[str], url: str) -> str:
    return f'<a href="{html.escape(url)}">{_escape_html(text)}</a>'


def truncate_address(address: Optional[str], prefix_len: int = 10, suffix_len: int = 10) -> str:
    if not address:
        return ""
    if len(address) <= prefix_len + suffix_len + 3:
        return address
    return f"{address[:prefix_len]}...{address[-suffix_len:]}"


def create_wallet_message(wallet: Any) -> str:
    name = getattr(wallet, "name", None) or "Wallet"
    blockchain = getattr(wallet, "blockchain", None)
    blockchain_text = getattr(blockchain, "value", str(blockchain)).upper() if blockchain else "UNKNOWN"
    address = getattr(wallet, "address", "")
    created_at = getattr(wallet, "created_at", None)
    balance = getattr(wallet, "balance", None)

    message = (
        f"{bold(name)}\n"
        f"{bold('Chain:')} {html.escape(blockchain_text)}\n"
        f"{bold('Address:')} {code(truncate_address(address))}\n"
    )
    if balance is not None:
        message += f"{bold('Balance:')} {html.escape(str(balance))}\n"
    if created_at:
        try:
            created = created_at.strftime("%Y-%m-%d")
            message += f"{bold('Created:')} {html.escape(created)}"
        except Exception:
            pass
    return message


def create_nft_message(nft: Any) -> str:
    status_emoji = {
        "pending": "⏳",
        "minted": "✅",
        "transferred": "↔️",
        "locked": "🔒",
        "burned": "🔥",
    }
    emoji = status_emoji.get(getattr(nft, "status", "pending"), "❓")

    message = (
        f"{emoji} {bold(getattr(nft, 'name', 'NFT'))}\n"
        f"{bold('ID:')} {code(getattr(nft, 'global_nft_id', ''))}\n"
        f"{bold('Status:')} {code(getattr(nft, 'status', ''))}\n"
        f"{bold('Chain:')} {html.escape(str(getattr(nft, 'blockchain', '')))}"
    )

    if getattr(nft, 'description', None):
        message += f"\n{bold('Description:')} {html.escape(str(nft.description))}"
    if getattr(nft, 'minted_at', None):
        try:
            minted = nft.minted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            message += f"\n{bold('Minted:')} {html.escape(minted)}"
        except Exception:
            pass
    if getattr(nft, 'token_id', None):
        message += f"\n{bold('Token ID:')} {code(getattr(nft, 'token_id'))}"
    return message

def create_wallet_buttons(wallets: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Adapter to keep compatibility with older callers expecting this helper
    return build_wallet_selector(wallets)



def build_wallet_selector(wallets: List[Dict[str, str]]) -> Dict[str, Any]:
    keyboard = []
    for wallet in wallets:
        wallet_text = f"{wallet.get('name', 'Wallet')} ({wallet.get('blockchain', 'Unknown')})"
        wallet_id = wallet.get('id', '')
        keyboard.append([{
            "text": wallet_text,
            "callback_data": f"select_wallet:{wallet_id}"
        }])
    
    if keyboard:
        keyboard.append([{"text": "❌ Cancel", "callback_data": "cancel"}])
    
    return {"inline_keyboard": keyboard}


def build_blockchain_selector(blockchains: Optional[List[str]] = None) -> Dict[str, Any]:
    if blockchains is None:
        blockchains = ["ethereum", "solana", "polygon", "ton", "bitcoin"]
    
    keyboard = []
    row = []
    for blockchain in blockchains:
        row.append({
            "text": f"🔗 {blockchain.capitalize()}",
            "callback_data": f"select_blockchain:{blockchain}"
        })
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([{"text": "❌ Cancel", "callback_data": "cancel"}])
    
    return {"inline_keyboard": keyboard}


def build_nft_actions_menu() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "📤 Transfer", "callback_data": "nft_transfer"},
                {"text": "🔥 Burn", "callback_data": "nft_burn"}
            ],
            [
                {"text": "🔒 Lock", "callback_data": "nft_lock"},
                {"text": "🔓 Unlock", "callback_data": "nft_unlock"}
            ],
            [{"text": "📢 List for Sale", "callback_data": "nft_list"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
    }


def build_marketplace_menu() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "📋 Browse Listings", "callback_data": "marketplace_browse"}],
            [{"text": "📢 List My NFT", "callback_data": "marketplace_list"}],
            [{"text": "💰 Make Offer", "callback_data": "marketplace_offer"}],
            [{"text": "📊 My Listings", "callback_data": "marketplace_mylistings"}],
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
    }


def build_confirmation_keyboard(action: str) -> Dict[str, Any]:
    action_safe = _escape_html(action)
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Confirm", "callback_data": f"confirm:{action}"},
                {"text": "❌ Cancel", "callback_data": "cancel"}
            ]
        ]
    }


def build_main_menu() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "🖼️ Mint NFT", "callback_data": "main_mint"}],
            [{"text": "👛 Wallets", "callback_data": "main_wallets"}],
            [{"text": "📋 My NFTs", "callback_data": "main_mynfts"}],
            [{"text": "🛍️ Marketplace", "callback_data": "main_marketplace"}],
            [{"text": "📚 Help", "callback_data": "main_help"}]
        ]
    }


def build_cancel_button() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "❌ Cancel", "callback_data": "cancel"}]
        ]
    }


def build_pagination_keyboard(
    page: int,
    total_pages: int,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append({"text": "⬅️ Previous", "callback_data": f"page:{page-1}:{item_id}"})
    
    nav_buttons.append({"text": f"{page}/{total_pages}", "callback_data": "page_info"})
    
    if page < total_pages:
        nav_buttons.append({"text": "Next ➡️", "callback_data": f"page:{page+1}:{item_id}"})
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([{"text": "❌ Done", "callback_data": "cancel"}])
    
    return {"inline_keyboard": keyboard}


def build_yes_no_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Yes", "callback_data": "confirm:yes"},
                {"text": "❌ No", "callback_data": "confirm:no"}
            ]
        ]
    }
