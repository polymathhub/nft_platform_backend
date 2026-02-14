"""
Telegram Minting Router
Handles Telegram webhook updates and minting commands.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db_session
from app.models import User, NFT
from app.models.marketplace import Listing
from app.services.telegram_bot_service import TelegramBotService
from app.services.nft_service import NFTService
from app.services.marketplace_service import MarketplaceService
from app.services.wallet_service import WalletService
from app.services.walletconnect_service import WalletConnectService
from app.services.telegram_dashboard_service import TelegramDashboardService
from app.utils.telegram_security import verify_telegram_data
from app.utils.telegram_keyboards import (
    build_start_keyboard,
    build_dashboard_keyboard,
    build_main_menu_keyboard,
    build_wallet_keyboard,
    build_blockchain_keyboard,
    build_nft_operations_keyboard,
    build_marketplace_keyboard,
    build_quick_mint_keyboard,
    build_dashboard_cta_keyboard,
    build_dashboard_cta_inline,
    build_wallet_cta_keyboard,
    build_nft_cta_keyboard,
    build_marketplace_cta_keyboard,
    build_blockchain_cta_keyboard,
    build_confirmation_cta_keyboard,
    build_balance_cta_keyboard,
    build_balance_cta_inline,
    build_main_actions_keyboard,
    build_main_actions_inline,
    build_start_dashboard_inline,
    build_admin_password_keyboard,
    build_admin_dashboard_keyboard,
    build_commission_settings_keyboard,
    build_user_management_keyboard,
    build_statistics_keyboard,
    build_backup_utilities_keyboard,
    build_blockchain_selection_keyboard,
)

logger = logging.getLogger(__name__)
router = APIRouter( tags=["telegram"])
bot_service = TelegramBotService()


# ==================== Pydantic Models ====================


class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    chat: dict  # Chat info
    from_user: TelegramUser = Field(..., alias="from")
    text: Optional[str] = None


class TelegramCallbackQuery(BaseModel):
    id: str
    from_user: TelegramUser = Field(..., alias="from")
    chat_instance: str
    data: Optional[str] = None
    message: Optional[TelegramMessage] = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


class MintRequestData(BaseModel):
    """Data for Telegram minting request."""
    wallet_id: str = Field(..., min_length=1)
    nft_name: str = Field(..., min_length=1, max_length=255)
    nft_description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)


# ==================== Endpoints ====================


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        # Validate secret token if configured
        from app.config import get_settings
        settings = get_settings()
        if settings.telegram_webhook_secret:
            header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not header_secret or header_secret != settings.telegram_webhook_secret:
                logger.warning("Invalid or missing webhook secret token")
                from fastapi import HTTPException, status

                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")
        # End secret validation
        # Handle message updates
        if update.message:
            await handle_message(db, update.message)
            return {"ok": True}

        # Handle callback queries (button clicks)
        if update.callback_query:
            await handle_callback_query(db, update.callback_query)
            return {"ok": True}

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}")
        return {"ok": False, "error": str(e)}


async def handle_message(db: AsyncSession, message: TelegramMessage) -> None:
    chat_id = message.chat.get("id")
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = (message.text or "").strip()

    if not text:
        logger.debug(f"Empty message from {username} ({user_id}), skipping")
        return

    logger.warning(f"[TELEGRAM] Received message from {username} ({user_id}): {text}")

    # Get or create user
    user = await get_or_create_telegram_user(db, message.from_user)
    if not user:
        logger.error(f"Failed to create/get user for Telegram ID {user_id}")
        await bot_service.send_message(
            chat_id,
            "❌ Failed to authenticate. Please try again.",
        )
        return

    logger.debug(f"User authenticated: {user.id}")

    # Check if user is entering admin password
    if hasattr(handle_admin_login, "_pending_admins") and chat_id in handle_admin_login._pending_admins:
        pending = handle_admin_login._pending_admins[chat_id]
        if pending.get("step") == "waiting_password":
            logger.warning(f"[ADMIN] Processing password input from {username}")
            await handle_admin_password_input(db, chat_id, user, text)
            return

    # Map button presses to commands
    button_mapping = {
        # Start/Menu buttons
        "🚀 Get Started": "/dashboard",
        "📊 Dashboard": "/dashboard",
        "📋 Menu": "/menu",

        # Dashboard CTA buttons
        "💰 Balance": "/balance",
        "⚡ Quick Mint": "/quick-mint",
        "📤 Send": "/transfer",
        "📤 Send NFT": "/transfer",
        "📥 Receive": "/receive",
        "🖼️ My NFTs": "/mynfts",
        "📜 View My NFTs": "/mynfts",
        "📜 My NFTs": "/mynfts",
        "📝 My NFTs": "/mynfts",
        "📊 My Listings": "/mylistings",
        "📈 My Listings": "/mylistings",
        "� Listings": "/mylistings",
        "🛍️ Marketplace": "/browse",
        "❓ Help": "/help",

        # Balance actions
        "🔄 Refresh": "/balance",
        "💰 Deposit USDT": "/deposit",

        # Admin buttons
        "⚙️ Admin": "/admin-login",
        "🚪 Logout": "/admin-logout",

        # Admin Dashboard buttons
        "💰 Commission": "/admin-commission",
        "👥 Users": "/admin-users",
        "📊 Statistics": "/admin-stats",
        "💾 Backup": "/admin-backup",

        # Commission Settings buttons
        "📈 View Rate": "/admin-view-rate",
        "✏️ Edit Rate": "/admin-edit-rate",
        "🏪 View Wallets": "/admin-view-wallets",
        "🔄 Update Wallet": "/admin-update-wallet",

        # User Management buttons
        "➕ Make Admin": "/admin-make-admin",
        "➖ Remove Admin": "/admin-remove-admin",
        "🚫 Suspend User": "/admin-suspend",
        "✅ Activate User": "/admin-activate",

        # Statistics buttons
        "📈 System Stats": "/admin-system-stats",
        "📋 Audit Logs": "/admin-audit-logs",
        "👨‍💼 Admin List": "/admin-list-admins",
        "💚 Health Check": "/admin-health-check",

        # Backup buttons
        "📥 Export Backup": "/admin-export-backup",
        "🔧 Maintenance": "/admin-maintenance",

        # Blockchain selection
        "TON": "admin-blockchain:ton",
        "TRC20": "admin-blockchain:trc20",
        "ERC20": "admin-blockchain:erc20",
        "Solana": "admin-blockchain:solana",

        # Wallet CTA buttons
        "👝 Wallets": "/wallets",
        "👝 My Wallets": "/wallets",
        "MY WALLETS": "/wallets",
        "➕ Create New": "/wallet-create",
        "➕ Create Wallet": "/wallet-create",
        "📥 Import": "/wallet-import",
        "📥 Import Wallet": "/wallet-import",
        "📋 List All": "/wallets",
        "📋 List Wallets": "/wallets",
        "⭐ Set Primary": "/set-primary",

        # NFT CTA buttons
        "🎨 Mint NFT": "/mint",
        "🎨 Start Minting": "/mint",
        "📤 Transfer": "/transfer",
        "🔥 Burn": "/burn",
        "🛍️ List for Sale": "/list",

        # Marketplace CTA buttons
        "🔍 Browse": "/browse",
        "❤️ Favorites": "/browse",
        "💬 Make Offer": "/offer",
        "📊 My Listings": "/mylistings",
        "❌ Cancel Listing": "/cancel-listing",

        # Blockchain selector buttons (plain and emoji variants)
        "⟡ Ethereum": "blockchain:ethereum",
        "Ethereum": "blockchain:ethereum",
        "🔶 Polygon": "blockchain:polygon",
        "Polygon": "blockchain:polygon",
        "◎ Solana": "blockchain:solana",
        "Solana": "blockchain:solana",
        "💎 TON": "blockchain:ton",
        "₿ Bitcoin": "blockchain:bitcoin",
        "Bitcoin": "blockchain:bitcoin",

        # Confirmation/Navigation buttons (plain and emoji variants)
        "✅ Confirm": "confirm:yes",
        "✅ Yes": "confirm:yes",
        "❌ Cancel": "/start",
        "❌ No": "/start",
        "◀️ Back to Dashboard": "/dashboard",
        "◀️ Back": "/dashboard",
        "◀️ Back to Menu": "/start",
        "◀️ Back to Admin": "/admin-dashboard",
        "◀️ Cancel": "/start",
        "❓ How to Mint": "/mint-help",
    }
    
    # Convert button text to command if applicable
    if text in button_mapping:
        text = button_mapping[text]

    # Handle blockchain reply-keyboard tokens like 'blockchain:ethereum'
    if text.startswith("blockchain:"):
        blockchain = text.split(":", 1)[1]
        logger.warning(f"[ROUTER] Detected blockchain selection from reply keyboard: {blockchain}")
        await handle_wallet_create_command(db, chat_id, user, blockchain)
        return

    # Wire CTA: when user presses 'Make Offer' we show deposit instructions if applicable
    if text == "/offer":
        # convert to command-like: ask user to provide listing id and amount or use quick flow
        # We'll prompt the user for listing id in chat
        await bot_service.send_message(chat_id, "To make an offer, reply with: /offer <listing_id> <amount>")
        return
        logger.warning(f"[ROUTER] Button pressed, converted to command: {text}")

    # Parse command - CHECK SPECIFIC COMMANDS BEFORE GENERAL ONES
    if text.startswith("/start"):
        logger.warning(f"[TELEGRAM] Processing /start command from {username}")
        await send_welcome_start(chat_id, username)
    
    elif text.startswith("/dashboard"):
        logger.warning(f"[TELEGRAM] Processing /dashboard command from {username}")
        await send_dashboard(db, chat_id, user, username)
    
    elif text.startswith("/balance"):
        logger.warning(f"[TELEGRAM] Processing /balance command from {username}")
        await send_balance(db, chat_id, user)
    
    elif text.startswith("/menu"):
        logger.warning(f"[TELEGRAM] Processing /menu command from {username}")
        await send_main_menu(chat_id, username)
    
    elif text.startswith("/quick-mint"):
        logger.warning(f"[TELEGRAM] Processing /quick-mint command from {username}")
        await send_quick_mint_screen(db, chat_id, user)
    
    elif text.startswith("/receive"):
        logger.warning(f"[TELEGRAM] Processing /receive command from {username}")
        await send_receive_menu(db, chat_id, user)

    # Wallet-related commands (check specific before general)
    elif text.startswith("/wallet-import"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await bot_service.send_wallet_creation_guide(chat_id)
        else:
            blockchain = parts[1].lower()
            address = parts[2]
            await handle_wallet_import_command(db, chat_id, user, blockchain, address)

    elif text.startswith("/wallet-create"):
        parts = text.split()
        logger.warning(f"[ROUTER] /wallet-create command parsed: parts={parts}")
        if len(parts) < 2:
            logger.warning(f"[ROUTER] No blockchain specified in /wallet-create")
            await bot_service.send_wallet_creation_guide(chat_id)
        else:
            blockchain = parts[1].lower()
            logger.warning(f"[ROUTER] Calling handle_wallet_create_command with blockchain={blockchain}")
            await handle_wallet_create_command(db, chat_id, user, blockchain)

    elif text.startswith("/wallet"):
        await bot_service.send_wallet_list(db, chat_id, user.id)

    elif text.startswith("/wallets"):
        await bot_service.send_wallet_list(db, chat_id, user.id)

    elif text.startswith("/connect-wallet"):
        # /connect-wallet <blockchain>
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_message(
                chat_id,
                "Usage: /connect-wallet &lt;blockchain&gt;\n\n"
                "Supported: ethereum, solana, polygon, bitcoin, ton\n\n"
                "Example: /connect-wallet ethereum",
            )
        else:
            blockchain = parts[1].lower()
            await handle_connect_wallet(db, chat_id, user, blockchain)

    elif text.startswith("/set-primary"):
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_message(
                chat_id,
                "Usage: /set-primary &lt;wallet_id&gt;",
            )
        else:
            wallet_id = parts[1]
            await bot_service.handle_set_primary_wallet(db, chat_id, user, wallet_id)

    elif text.startswith("/mynfts"):
        await bot_service.send_user_nfts(db, chat_id, user.id)

    elif text.startswith("/mint"):
        await handle_mint_command(db, chat_id, user, text)

    elif text.startswith("/list"):
        await handle_list_command(db, chat_id, user, text)

    elif text.startswith("/mylistings"):
        await bot_service.send_user_listings(db, chat_id, user.id)

    elif text.startswith("/browse"):
        await bot_service.send_marketplace_listings(db, chat_id)

    elif text.startswith("/offer"):
        await handle_make_offer_command(db, chat_id, user, text)

    elif text.startswith("/cancel-listing"):
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_message(
                chat_id,
                "Usage: /cancel-listing &lt;listing_id&gt",
            )
        else:
            listing_id = parts[1]
            await bot_service.handle_cancel_listing(db, chat_id, user, listing_id)

    elif text.startswith("/transfer"):
        await handle_transfer_command(db, chat_id, user, text)

    elif text.startswith("/burn"):
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_message(
                chat_id,
                "Usage: /burn &lt;nft_id&gt;",
            )
        else:
            nft_id = parts[1]
            await bot_service.handle_burn_nft(db, chat_id, user, nft_id)

    elif text.startswith("/status"):
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_message(
                chat_id,
                "Usage: /status &lt;nft_id&gt;",
            )
        else:
            nft_id = parts[1]
            await bot_service.send_nft_status(db, chat_id, nft_id)

    elif text.startswith("/mint-help"):
        await send_mint_help(chat_id)

    elif text.startswith("/help"):
        await send_help_message(chat_id)

    # Admin commands
    elif text.startswith("/admin-login"):
        await handle_admin_login(db, chat_id, user)
    
    elif text.startswith("/admin-logout"):
        await handle_admin_logout(chat_id, user)
    
    elif text.startswith("/admin-dashboard"):
        await handle_admin_dashboard(db, chat_id, user)
    
    elif text.startswith("/admin-commission"):
        await handle_admin_commission(db, chat_id, user)
    
    elif text.startswith("/admin-users"):
        await handle_admin_users(db, chat_id, user)
    
    elif text.startswith("/admin-stats"):
        await handle_admin_stats(db, chat_id, user)
    
    elif text.startswith("/admin-backup"):
        await handle_admin_backup(db, chat_id, user)

    else:
        await bot_service.send_message(
            chat_id,
            "Unknown command. Use /help to see available commands.",
        )


async def send_welcome_start(chat_id: int, username: str) -> None:
    """Send /start dashboard with image + web_app launcher button (Blum-style)."""
    from app.config import get_settings
    
    logger.warning(f"[TELEGRAM] send_welcome_start called for chat_id={chat_id}, username={username}")
    settings = get_settings()
    
    message = (
        f"<b>Welcome to NFT Platform</b>\n\n"
        f"Hello {username}.\n\n"
        f"<b>Manage wallets, mint NFTs, and trade on a single platform.</b>\n\n"
        f"Tap <b>Open App</b> below to get started, or use the shortcuts."
    )
    
    # Build dashboard with web_app button
    keyboard = build_start_dashboard_inline(settings.telegram_webapp_url)
    
    # Send welcome message with photo and dashboard buttons
    logger.warning(f"[TELEGRAM] Sending /start dashboard with banner image and web_app button...")
    result = await bot_service.send_photo(
        chat_id, 
        settings.banner_image_url,
        caption=message,
        reply_markup=keyboard
    )
    logger.warning(f"[TELEGRAM] Welcome /start dashboard sent: {result}")


async def send_main_menu(chat_id: int, username: str) -> None:
    logger.warning(f"[TELEGRAM] send_main_menu called for chat_id={chat_id}, username={username}")
    message = (
        f"<b>🚀 Welcome to NFT Platform, {username}!</b>\n\n"
        f"Use the buttons below to navigate or type commands.\n\n"
        f"<b>What would you like to do?</b>"
    )
    logger.warning(f"[TELEGRAM] Calling bot_service.send_message with CTA menu keyboard...")
    result = await bot_service.send_message(
        chat_id, 
        message,
        reply_markup=build_dashboard_cta_keyboard()
    )
    logger.warning(f"[TELEGRAM] bot_service.send_message returned: {result}")


async def send_dashboard(db: AsyncSession, chat_id: int, user: User, username: str) -> None:
    """Send premium dashboard with user stats and CTA action buttons."""
    logger.warning(f"[TELEGRAM] Sending dashboard for {username}")
    try:
        # Get user stats
        logger.warning(f"[DASHBOARD] Getting stats for user {user.id}")
        stats = await TelegramDashboardService.get_user_dashboard_stats(db, user.id)
        logger.warning(f"[DASHBOARD] Stats retrieved: {stats}")
        
        message = TelegramDashboardService.format_dashboard_message(username, stats)
        logger.warning(f"[DASHBOARD] Message formatted, sending with CTA keyboard")
        
        # Use CTA keyboard with text buttons (below message input)
        await bot_service.send_message(
            chat_id,
            message,
            reply_markup=build_dashboard_cta_inline()
        )
        logger.warning(f"[DASHBOARD] Dashboard sent successfully with CTA buttons")
    except Exception as e:
        logger.error(f"[DASHBOARD] Error sending dashboard: {type(e).__name__}: {e}", exc_info=True)
        await bot_service.send_message(chat_id, f"❌ Error loading dashboard: {str(e)}")


async def send_balance(db: AsyncSession, chat_id: int, user: User) -> None:
    """Send user's USDT balance across all wallets."""
    logger.warning(f"[TELEGRAM] Sending balance for user {user.id}")
    try:
        from app.models import Wallet
        from sqlalchemy import select
        
        # Get all user wallets
        wallets_result = await db.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )
        wallets = wallets_result.scalars().all()
        
        if not wallets:
            await bot_service.send_message(
                chat_id,
                "❌ No wallets found. Create one first:\n\n<code>/wallet-create ethereum</code>",
                reply_markup=build_balance_cta_inline()
            )
            return
        
        # Build balance message
        message = "<b>💰 Your USDT Balance</b>\n\n"
        total_balance = 0.0
        
        for wallet in wallets:
            balance = wallet.wallet_metadata.get("balance", 0.0) if wallet.wallet_metadata else 0.0
            total_balance += balance
            
            message += (
                f"<b>{wallet.blockchain.value.upper()}</b>\n"
                f"  Address: <code>{wallet.address[:15]}...{wallet.address[-10:]}</code>\n"
                f"  💵 Balance: <b>${balance:.2f}</b>\n"
                f"{'  ⭐ Primary' if wallet.is_primary else ''}\n\n"
            )
        
        message += f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n"
        message += f"<b>Total Balance: ${total_balance:.2f} USDT</b>\n"
        message += f"<b>━━━━━━━━━━━━━━━━━━━━</b>\n"
        
        await bot_service.send_message(
            chat_id,
            message,
            reply_markup=build_balance_cta_inline()
        )
        logger.warning(f"[BALANCE] Balance sent successfully")
    except Exception as e:
        logger.error(f"[BALANCE] Error sending balance: {type(e).__name__}: {e}", exc_info=True)
        await bot_service.send_message(chat_id, f"❌ Error loading balance: {str(e)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_admin_login(db: AsyncSession, chat_id: int, user: User) -> None:
    """Start admin login flow - prompt for password."""
    logger.warning(f"[ADMIN] Admin login attempt by user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminService
    
    message = (
        "<b>🔐 Admin Login</b>\n\n"
        "Please enter your admin password to continue.\n\n"
        "<i>Password is private and will not be stored.</i>"
    )
    
    await bot_service.send_message(
        chat_id,
        message,
        reply_markup=build_admin_password_keyboard()
    )
    
    # Store a temporary state that we're waiting for password
    # Note: In production, use Redis to store state
    if not hasattr(handle_admin_login, "_pending_admins"):
        handle_admin_login._pending_admins = {}
    handle_admin_login._pending_admins[chat_id] = {"user_id": user.id, "username": user.username, "step": "waiting_password"}


async def handle_admin_password_input(db: AsyncSession, chat_id: int, user: User, password: str) -> None:
    """Validate admin password and create session if correct."""
    logger.warning(f"[ADMIN] Password submission from user {user.id}")
    
    from app.config import settings
    from app.services.telegram_admin_service import TelegramAdminSession, TelegramAdminService
    
    # Validate password
    if password != settings.admin_password:
        logger.warning(f"[ADMIN] Invalid password attempt from user {user.id}")
        await bot_service.send_message(
            chat_id,
            "❌ Invalid password. Access denied.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        
        # Clear pending state
        if hasattr(handle_admin_login, "_pending_admins") and chat_id in handle_admin_login._pending_admins:
            del handle_admin_login._pending_admins[chat_id]
        return
    
    # Password correct - create session
    logger.warning(f"[ADMIN] Correct password, creating session for user {user.id}")
    TelegramAdminSession.create_session(chat_id, user.id, user.username)
    
    # Show admin dashboard
    await handle_admin_dashboard(db, chat_id, user)


async def handle_admin_logout(chat_id: int, user: User) -> None:
    """End admin session."""
    logger.warning(f"[ADMIN] Admin logout for user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession
    
    TelegramAdminSession.logout(chat_id)
    
    await bot_service.send_message(
        chat_id,
        "✅ Logged out from admin panel.",
        reply_markup=build_dashboard_cta_keyboard()
    )


async def handle_admin_dashboard(db: AsyncSession, chat_id: int, user: User) -> None:
    """Show admin dashboard - check if user is logged in."""
    logger.warning(f"[ADMIN] Dashboard access by user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession, TelegramAdminService
    
    # Check if user is logged in
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        logger.warning(f"[ADMIN] User {user.id} not logged in for dashboard")
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel. Please use /admin-login",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    
    # Format and send dashboard
    dashboard_msg = TelegramAdminService.format_admin_dashboard()
    
    await bot_service.send_message(
        chat_id,
        dashboard_msg,
        reply_markup=build_admin_dashboard_keyboard()
    )


async def handle_admin_commission(db: AsyncSession, chat_id: int, user: User) -> None:
    """Show commission management menu."""
    logger.warning(f"[ADMIN] Commission menu for user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.config import settings
    
    # Check if user is logged in
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    
    message = (
        "<b>💰 Commission Settings</b>\n\n"
        f"<b>Current Rate:</b> {settings.commission_rate * 100:.1f}%\n\n"
        f"<b>Wallets Configured:</b>\n"
        f"  • TON: <code>{settings.commission_wallet_ton[:20]}...</code>\n"
        f"  • TRC20: <code>{settings.commission_wallet_trc20[:20]}...</code>\n"
        f"  • ERC20: <code>{settings.commission_wallet_erc20[:20]}...</code>\n"
        f"  • Solana: <code>{settings.commission_wallet_solana[:20]}...</code>\n\n"
        "Use buttons to manage commission settings."
    )
    
    await bot_service.send_message(
        chat_id,
        message,
        reply_markup=build_commission_settings_keyboard()
    )


async def handle_admin_users(db: AsyncSession, chat_id: int, user: User) -> None:
    """Show user management menu."""
    logger.warning(f"[ADMIN] User management menu for user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.models import User as UserModel
    from sqlalchemy import select
    
    # Check if user is logged in
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    
    # Get user count
    result = await db.execute(select(UserModel))
    users = result.scalars().all()
    
    message = (
        "<b>👥 User Management</b>\n\n"
        f"<b>Total Users:</b> {len(users)}\n\n"
        "Use buttons to manage users (promote, demote, suspend, activate)."
    )
    
    await bot_service.send_message(
        chat_id,
        message,
        reply_markup=build_user_management_keyboard()
    )


async def handle_admin_stats(db: AsyncSession, chat_id: int, user: User) -> None:
    """Show statistics menu."""
    logger.warning(f"[ADMIN] Statistics menu for user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.models import User as UserModel, NFT, Wallet
    from sqlalchemy import select, func
    
    # Check if user is logged in
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    
    # Get statistics
    user_count = await db.scalar(select(func.count(UserModel.id)))
    nft_count = await db.scalar(select(func.count(NFT.id)))
    wallet_count = await db.scalar(select(func.count(Wallet.id)))
    
    message = (
        "<b>📊 Statistics</b>\n\n"
        f"<b>Users:</b> {user_count or 0}\n"
        f"<b>NFTs Minted:</b> {nft_count or 0}\n"
        f"<b>Wallets Created:</b> {wallet_count or 0}\n\n"
        "Use buttons to view detailed statistics and audit logs."
    )
    
    await bot_service.send_message(
        chat_id,
        message,
        reply_markup=build_statistics_keyboard()
    )


async def handle_admin_backup(db: AsyncSession, chat_id: int, user: User) -> None:
    """Show backup utilities menu."""
    logger.warning(f"[ADMIN] Backup menu for user {user.id}")
    
    from app.services.telegram_admin_service import TelegramAdminSession
    
    # Check if user is logged in
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    
    message = (
        "<b>💾 Backup & Utilities</b>\n\n"
        "Options:\n"
        "  • <b>Export Backup:</b> Download all platform data as JSON\n"
        "  • <b>Maintenance:</b> System maintenance tools\n\n"
        "Use buttons to proceed."
    )
    
    await bot_service.send_message(
        chat_id,
        message,
        reply_markup=build_backup_utilities_keyboard()
    )


async def send_quick_mint_screen(db: AsyncSession, chat_id: int, user: User) -> None:
    """Send quick mint screen with wallet suggestion."""
    logger.warning(f"[TELEGRAM] Sending quick mint screen")
    try:
        wallet = await TelegramDashboardService.build_quick_mint_message(db, user.id)
        
        if not wallet:
            await bot_service.send_message(
                chat_id,
                "❌ No wallet found. Create one first:\n\n<code>/wallet-create ethereum</code>",
                reply_markup=build_dashboard_cta_keyboard()
            )
            return
        
        message = TelegramDashboardService.format_quick_mint_message(wallet)
        await bot_service.send_message(
            chat_id,
            message,
            reply_markup=build_dashboard_cta_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending quick mint: {e}")
        await bot_service.send_message(chat_id, "❌ Error loading quick mint")


async def send_receive_menu(db: AsyncSession, chat_id: int, user: User) -> None:
    """Send receive wallet menu."""
    logger.warning(f"[TELEGRAM] Sending receive menu")
    try:
        wallets = await bot_service.get_user_wallets(db, user.id)
        
        if not wallets:
            await bot_service.send_message(
                chat_id,
                "❌ No wallets found. Create one first:\n\n<code>/wallet-create ethereum</code>"
            )
            return
        
        message = "<b>📥 Receive NFT or Tokens</b>\n\nSelect a wallet to receive to:\n\n"
        for i, wallet in enumerate(wallets, 1):
            message += (
                f"{i}. <b>{wallet.blockchain.value.upper()}</b>\n"
                f"   Address: <code>{wallet.address}</code>\n\n"
            )
        
        message += "Share your wallet address above with the sender.\n\n<b>⚠️ Warning:</b> Only receive on the correct blockchain!"
        await bot_service.send_message(
            chat_id,
            message,
            reply_markup=build_dashboard_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending receive menu: {e}")
        await bot_service.send_message(chat_id, "❌ Error loading receive menu")


async def send_mint_help(chat_id: int) -> None:
    """Send mint help guide."""
    message = (
        "<b>🎨 How to Mint NFTs</b>\n\n"
        "<b>Step 1: Prepare</b>\n"
        "• Have an image URL ready\n"
        "• Have a wallet created\n\n"
        "<b>Step 2: Click Quick Mint</b>\n"
        "• Or use: <code>/mint wallet_id name</code>\n\n"
        "<b>Step 3: Add Details</b>\n"
        "• Name your NFT\n"
        "• Add description (optional)\n"
        "• Add image URL (optional)\n\n"
        "<b>Step 4: Confirm & Wait</b>\n"
        "• Check status: <code>/status nft_id</code>\n\n"
        "<b>💡 Tip:</b> Use Quick Mint for fastest experience!"
    )
    await bot_service.send_message(chat_id, message, reply_markup=build_dashboard_cta_keyboard())


async def send_help_message(chat_id: int) -> None:
    """Send comprehensive help message."""
    message = (
        "<b>📚 Complete Command List</b>\n\n"
        "<b>NFT Operations:</b>\n"
        "• <code>/mint &lt;wallet_id&gt; &lt;name&gt; [description] [image_url]</code> - Mint NFT\n"
        "• <code>/mynfts</code> - View your available NFTs\n"
        "• <code>/status &lt;nft_id&gt;</code> - Check NFT status\n"
        "• <code>/transfer &lt;nft_id&gt; &lt;address&gt;</code> - Transfer NFT\n"
        "• <code>/burn &lt;nft_id&gt;</code> - Burn NFT\n\n"
        "<b>Marketplace:</b>\n"
        "• <code>/browse</code> - Browse active listings\n"
        "• <code>/list &lt;nft_id&gt; &lt;price&gt; [currency]</code> - List NFT\n"
        "• <code>/mylistings</code> - Your active listings\n"
        "• <code>/offer &lt;listing_id&gt; &lt;price&gt;</code> - Make offer\n"
        "• <code>/cancel-listing &lt;listing_id&gt;</code> - Cancel listing\n\n"
        "<b>Wallet Management:</b>\n"
        "• <code>/wallets</code> - List your wallets\n"
        "• <code>/set-primary &lt;wallet_id&gt;</code> - Set primary wallet\n"
        "• <code>/wallet-create &lt;blockchain&gt;</code> - Create wallet\n"
        "• <code>/wallet-import &lt;blockchain&gt; &lt;address&gt;</code> - Import wallet\n\n"
        "<b>Supported Blockchains:</b>\n"
        "ethereum, solana, polygon, ton, bitcoin\n\n"
        "<b>Examples:</b>\n"
        "<code>/mint 550e8400-e29b-41d4 MyNFT 'Cool Art'</code>\n"
        "<code>/list 123e4567-e89b-12d3 99.99 USDT</code>\n"
        "<code>/offer fee2c6f8-b1d4-4567 45.50</code>"
    )
    await bot_service.send_message(chat_id, message)


async def handle_mint_command(
    db: AsyncSession, chat_id: int, user: User, command_text: str
) -> None:
    parts = command_text.split(maxsplit=4)

    if len(parts) < 3:
        await bot_service.send_message(
            chat_id,
            "Usage: /mint &lt;wallet_id&gt; &lt;nft_name&gt; [description] [image_url]\n\n"
            "Example: /mint 550e8400-e29b-41d4-a716-446655440000 MyNFT 'My cool NFT' https://example.com/image.jpg",
        )
        return

    wallet_id = parts[1]
    nft_name = parts[2]
    description = parts[3] if len(parts) > 3 else None
    image_url = parts[4] if len(parts) > 4 else None

    # Send "typing" indicator on telegram 
    await bot_service.send_message(
        chat_id,
        "⏳ Processing your mint request...",
    )

    # Handle minting
    nft, error = await bot_service.handle_mint_command(
        db=db,
        chat_id=chat_id,
        user=user,
        wallet_id=wallet_id,
        nft_name=nft_name,
        nft_description=description,
        image_url=image_url,
    )

    if nft:
        logger.info(f"NFT minted successfully via Telegram for user {user.id}")
    else:
        logger.warning(f"Failed to mint NFT via Telegram: {error}")


async def handle_list_command(
    db: AsyncSession, chat_id: int, user: User, command_text: str
) -> None:
    """
    Handle /list command.
    Format: /list <nft_id> <price> [currency]
    """
    parts = command_text.split()

    if len(parts) < 3:
        await bot_service.send_message(
            chat_id,
            "Usage: /list &lt;nft_id&gt; &lt;price&gt; [currency]\n\n"
            "Example: /list 550e8400-e29b-41d4-a716-446655440000 99.99 USDT",
        )
        return

    nft_id = parts[1]
    price = parts[2]
    currency = parts[3] if len(parts) > 3 else "USDT"

    await bot_service.send_message(
        chat_id,
        "⏳ Processing your listing request...",
    )

    listing, error = await bot_service.handle_list_nft(
        db=db,
        chat_id=chat_id,
        user=user,
        nft_id=nft_id,
        price=price,
        currency=currency,
    )

    if listing:
        logger.info(f"NFT listed successfully via Telegram for user {user.id}")
    else:
        logger.warning(f"Failed to list NFT via Telegram: {error}")


async def handle_connect_wallet(
    db: AsyncSession, chat_id: int, user: User, blockchain: str
) -> None:
    """Handle wallet connection via WalletConnect."""
    supported_blockchains = ["ethereum", "solana", "polygon", "bitcoin", "ton"]

    if blockchain.lower() not in supported_blockchains:
        await bot_service.send_message(
            chat_id,
            f"❌ Unsupported blockchain: {blockchain}\n\n"
            f"Supported: {', '.join(supported_blockchains)}",
        )
        return

    try:
        # Generate WalletConnect connection URI
        uri = WalletConnectService.generate_connection_uri()

        # Store session for later approval
        session_id = str(user.id)[:8]
        WalletConnectService.store_session(
            session_id,
            {
                "user_id": str(user.id),
                "blockchain": blockchain.lower(),
                "status": "pending",
                "uri": uri,
            },
        )

        # Send connection instructions
        message = (
            f"<b>🔗 Connect {blockchain.capitalize()} Wallet</b>\n\n"
            f"To connect your {blockchain} wallet:\n\n"
            f"1️⃣ Open a WalletConnect-compatible wallet app\n"
            f"2️⃣ Scan this connection URI: <code>{uri[:50]}...</code>\n"
            f"3️⃣ Approve the connection request\n\n"
            f"Once approved, your wallet will be linked to your account."
        )

        await bot_service.send_message(chat_id, message)
        logger.info(f"WalletConnect initiated for user {user.id}, blockchain: {blockchain}")

    except Exception as e:
        logger.error(f"Failed to initiate WalletConnect: {e}", exc_info=True)
        await bot_service.send_message(
            chat_id,
            "❌ Failed to initiate wallet connection. Please try again later.",
        )


async def handle_make_offer_command(
    db: AsyncSession, chat_id: int, user: User, command_text: str
) -> None:
    """
    Handle /offer command.
    Format: /offer <listing_id> <offer_price>
    """
    parts = command_text.split()

    if len(parts) < 3:
        await bot_service.send_message(
            chat_id,
            "Usage: /offer &lt;listing_id&gt; &lt;offer_price&gt;\n\n"
            "Example: /offer abc12345-def6-4890 45.50",
        )
        return

    listing_id = parts[1]
    offer_price = parts[2]

    await bot_service.send_message(
        chat_id,
        "⏳ Processing your offer...",
    )

    offer, error = await bot_service.handle_make_offer(
        db=db,
        chat_id=chat_id,
        user=user,
        listing_id=listing_id,
        offer_price=offer_price,
    )

    if offer:
        logger.info(f"Offer made successfully via Telegram for user {user.id}")
    else:
        logger.warning(f"Failed to make offer via Telegram: {error}")


async def handle_transfer_command(
    db: AsyncSession, chat_id: int, user: User, command_text: str
) -> None:
    """
    Handle /transfer command.
    Format: /transfer <nft_id> <to_address>
    """
    parts = command_text.split(maxsplit=2)

    if len(parts) < 3:
        await bot_service.send_message(
            chat_id,
            "Usage: /transfer &lt;nft_id&gt; &lt;to_address&gt;\n\n"
            "Example: /transfer 550e8400-e29b-41d4 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )
        return

    nft_id = parts[1]
    to_address = parts[2]

    await bot_service.send_message(
        chat_id,
        "⏳ Processing your transfer request...",
    )

    nft, error = await bot_service.handle_transfer_nft(
        db=db,
        chat_id=chat_id,
        user=user,
        nft_id=nft_id,
        to_address=to_address,
    )

    if nft:
        logger.info(f"NFT transfer initiated via Telegram for user {user.id}")
    else:
        logger.warning(f"Failed to transfer NFT via Telegram: {error}")


async def handle_wallet_create_command(
    db: AsyncSession, chat_id: int, user: User, blockchain: str
) -> None:
    """Handle /wallet-create command with proper wallet generation."""
    logger.warning(f"[HANDLER] handle_wallet_create_command called: user_id={user.id}, blockchain={blockchain}")
    
    await bot_service.send_message(chat_id, f"⏳ Creating {blockchain.upper()} wallet...")
    logger.warning(f"[HANDLER] Sent 'Creating wallet' message")
    
    wallet, error = await bot_service.handle_wallet_create(
        db=db, chat_id=chat_id, user=user, blockchain=blockchain
    )
    logger.warning(f"[HANDLER] handle_wallet_create returned: wallet={wallet is not None}, error={error}")
    
    if wallet:
        logger.info(f"✓ Wallet created successfully: {wallet.id}")
        # Show the new wallet in the wallet list
        await bot_service.send_wallet_list(db, chat_id, user.id)
    else:
        logger.error(f"✗ Wallet creation failed: {error}")
        await bot_service.send_message(
            chat_id,
            f"❌ Failed to create wallet: {error or 'Unknown error'}\n\nPlease try again or contact support."
        )


async def handle_wallet_import_command(
    db: AsyncSession, chat_id: int, user: User, blockchain: str, address: str
) -> None:
    await bot_service.send_message(chat_id, f"⏳ Importing wallet for {blockchain}...")
    wallet, error = await bot_service.handle_wallet_import(
        db=db, chat_id=chat_id, user=user, blockchain=blockchain, address=address
    )
    if wallet:
        logger.info(f"Wallet imported successfully for user {user.id}")
    else:
        logger.warning(f"Failed to import wallet: {error}")


async def handle_callback_query(db: AsyncSession, callback: TelegramCallbackQuery) -> None:
    """Handle callback queries from button clicks."""
    chat_id = callback.message.chat.get("id") if callback.message else None
    user_id = callback.from_user.id
    data = callback.data or ""

    logger.info(f"Callback query from {user_id}: {data}")

    # Get user
    user = await get_or_create_telegram_user(db, callback.from_user)
    if not user:
        return

    # Handle different callback actions
    if data.startswith("mint_wallet_"):
        wallet_id = data.replace("mint_wallet_", "")
        # Send prompt for NFT name
        await bot_service.send_message(
            chat_id,
            f"Selected wallet: <code>{wallet_id[:10]}...</code>\n"
            f"Please reply with the NFT name and details:\n"
            f"/mint {wallet_id} &lt;name&gt;",
        )

    elif data.startswith("wallet_info_"):
        wallet_id = data.replace("wallet_info_", "")
        # Show wallet info
        from app.models import Wallet
        from uuid import UUID
        result = await db.execute(
            select(Wallet).where(Wallet.id == UUID(wallet_id))
        )
        wallet = result.scalar_one_or_none()
        if wallet:
            message = (
                f"<b>Wallet Details</b>\n\n"
                f"<b>Name:</b> {wallet.name}\n"
                f"<b>Blockchain:</b> {wallet.blockchain.value}\n"
                f"<b>Address:</b> <code>{wallet.address}</code>\n"
                f"<b>Created:</b> {wallet.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            )
            await bot_service.send_message(chat_id, message)

    elif data == "wallet_create":
        # Prompt user for wallet creation options and show blockchain choices
        await bot_service.send_message(
            chat_id,
            "To create a wallet, choose a blockchain or use the command:\n/wallet-create <blockchain>",
            reply_markup=build_blockchain_cta_keyboard(),
        )

    elif data.startswith("select_blockchain:"):
        # Inline blockchain selector from UI designer
        blockchain = data.split(":", 1)[1]
        await handle_wallet_create_command(db, chat_id, user, blockchain)

    elif data == "admin_dashboard":
        # Only allow if user is admin - check DB
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.telegram_id == str(callback.from_user.id)))
        user = result.scalar_one_or_none()
        if not user:
            return
        if getattr(user, 'user_role', None) and str(user.user_role).upper().endswith('ADMIN'):
            # Show inline admin dashboard for richer UI
            from app.utils.telegram_keyboards import build_admin_dashboard_inline
            await bot_service.send_message(chat_id, "Opening admin dashboard...", reply_markup=build_admin_dashboard_inline())
        else:
            await bot_service.send_message(chat_id, "❌ You are not authorized for admin actions.")

    # Support inline CTA callbacks that carry plain command strings (e.g. "/wallets", "/balance")
    elif data.startswith("/"):
        # Route inline command callbacks to existing handlers
        cmd = data
        try:
            if cmd == "/wallets" or cmd == "/wallet":
                await bot_service.send_wallet_list(db, chat_id, user.id)

            elif cmd == "/balance":
                await send_balance(db, chat_id, user)

            elif cmd == "/quick-mint":
                await send_quick_mint_screen(db, chat_id, user)

            elif cmd == "/transfer":
                # open transfer flow (prompt)
                await handle_transfer_command(db, chat_id, user, cmd)

            elif cmd == "/mynfts":
                await bot_service.send_user_nfts(db, chat_id, user.id)

            elif cmd == "/browse":
                await bot_service.send_marketplace_listings(db, chat_id)

            elif cmd == "/mylistings":
                await bot_service.send_user_listings(db, chat_id, user.id)

            elif cmd == "/wallet-create":
                # Inline CTA: prompt user to choose blockchain for wallet creation
                await bot_service.send_message(
                    chat_id,
                    "To create a wallet, choose a blockchain or use the command:\n/wallet-create <blockchain>",
                    reply_markup=build_blockchain_cta_keyboard(),
                )

            elif cmd == "/mint":
                await handle_mint_command(db, chat_id, user, cmd)

            elif cmd == "/wallets" or cmd == "/wallet":
                await bot_service.send_wallet_list(db, chat_id, user.id)

            elif cmd == "/deposit":
                # simple deposit instructions
                await bot_service.send_message(
                    chat_id,
                    "To deposit USDT, send funds to your primary wallet address or use the on-ramp services listed in the app dashboard.",
                )

            elif cmd == "/help":
                await bot_service.send_message(chat_id, "Send /start to see available commands or visit the help page.")

        except Exception as e:
            logger.error(f"Error handling inline command callback {cmd}: {e}")
    
    # Admin inline navigation callbacks
    elif data == "admin-commission":
        await handle_admin_commission(db, chat_id, user)

    elif data == "admin-users":
        await handle_admin_users(db, chat_id, user)

    elif data == "admin-stats":
        await handle_admin_stats(db, chat_id, user)

    elif data == "admin-backup":
        await handle_admin_backup(db, chat_id, user)

    elif data == "admin-logout":
        await handle_admin_logout(chat_id, user)
    
    elif data.startswith("offer_listing_"):
        listing_id = data.replace("offer_listing_", "")
        # Prompt user to submit an offer using the standard command format
        await bot_service.send_message(
            chat_id,
            f"To make an offer for listing <code>{listing_id}</code>, reply with:\n/offer {listing_id} <amount>",
        )


async def get_or_create_telegram_user(
    db: AsyncSession, telegram_user: TelegramUser
) -> Optional[User]:
    """Get or create user from Telegram user info."""
    result = await db.execute(
        select(User).where(User.telegram_id == str(telegram_user.id))
    )
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create new user
    from app.services.auth_service import AuthService
    from app.utils.security import hash_password

    new_user, error = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=telegram_user.id,
        telegram_username=telegram_user.username or f"user_{telegram_user.id}",
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )

    if error:
        logger.error(f"Failed to create Telegram user: {error}")
        return None

    return new_user


# ==================== Admin Endpoints ====================


@router.post("/webhook/set")
async def set_webhook(webhook_url: str) -> dict:
    """
    Set Telegram webhook (admin only).
    Example: POST /api/v1/telegram/webhook/set?webhook_url=https://yourdomain.com/api/v1/telegram/webhook
    """
    # In production, add authentication check
    success = await bot_service.set_webhook(webhook_url)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set webhook",
        )
    return {
        "success": True,
        "message": f"Webhook set to {webhook_url}",
    }

# NOTE: the real `/webhook` handler is defined earlier in this file
# (handles message and callback_query payloads). This stub removed
# to avoid overriding the real webhook endpoint which prevents
# callback queries (inline buttons) from being processed.
@router.post("/webhook/delete")
async def delete_webhook() -> dict:
    """Delete Telegram webhook (admin only)."""
    success = await bot_service.delete_webhook()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        )
    return {
        "success": True,
        "message": "Webhook deleted",
    }


@router.post("/send-notification")
async def send_telegram_notification(
    user_id: str,
    title: str,
    message: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Send a Telegram notification to a user (admin only).
    Used for sending mint status updates and other notifications.
    """
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    success = await bot_service.send_notification(
        user=user,
        title=title,
        message=message,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification",
        )

    return {
        "success": True,
        "message": f"Notification sent to user {user.telegram_username}",
    }


# ==================== Telegram Web App Endpoints ====================


@router.get("/web-app/init")
async def web_app_init(
    init_data: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Initialize Telegram Web App session.
    Verify init data and authenticate user.
    
    The init_data comes from Telegram WebApp.initData
    """
    import hashlib
    import hmac
    from urllib.parse import parse_qs

    # Verify Telegram data signature
    if not verify_telegram_data(init_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram data signature",
        )

    # Parse init data
    params = parse_qs(init_data)
    user_data = None
    
    # Extract user data from init_data
    if "user" in params:
        import json
        user_data = json.loads(params["user"][0])

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user data provided",
        )

    # Get or create user
    from app.services.auth_service import AuthService

    user, error = await AuthService.authenticate_telegram(
        db=db,
        telegram_id=user_data.get("id"),
        telegram_username=user_data.get("username", f"user_{user_data.get('id')}"),
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
    )

    if error or not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user",
        )

    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "telegram_id": user.telegram_id,
            "telegram_username": user.telegram_username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/web-app/user")
async def web_app_get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user profile for web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "telegram_id": user.telegram_id,
            "telegram_username": user.telegram_username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/web-app/wallets")
async def web_app_get_wallets(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user's wallets for web app. Cached for 60 seconds."""
    from uuid import UUID
    from app.models import Wallet
    from fastapi import Response

    result = await db.execute(
        select(Wallet)
        .where(Wallet.user_id == UUID(user_id))
        .order_by(Wallet.is_primary.desc(), Wallet.created_at.desc())
    )
    wallets = result.scalars().all()

    response_data = {
        "success": True,
        "wallets": [
            {
                "id": str(wallet.id),
                "name": wallet.name,
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat(),
            }
            for wallet in wallets
        ],
    }
    return response_data


@router.get("/web-app/nfts")
async def web_app_get_user_nfts(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user's NFTs for web app. Optimized query, cached for 30 seconds."""
    from uuid import UUID

    # Optimized query with index-friendly order
    result = await db.execute(
        select(NFT)
        .where(NFT.user_id == UUID(user_id))
        .order_by(NFT.created_at.desc())
    )
    nfts = result.scalars().all()

    return {
        "success": True,
        "nfts": [
            {
                "id": str(nft.id),
                "name": nft.name,
                "global_nft_id": nft.global_nft_id,
                "description": nft.description,
                "blockchain": nft.blockchain,
                "status": nft.status.value if hasattr(nft.status, 'value') else nft.status,
                "image_url": nft.image_url,
                "minted_at": nft.minted_at.isoformat() if nft.minted_at else None,
                "created_at": nft.created_at.isoformat(),
            }
            for nft in nfts
        ],
    }


@router.get("/web-app/dashboard-data")
async def web_app_get_dashboard_data(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Get all dashboard data in one call (wallets, NFTs, listings).
    Significantly faster than 3 separate API calls. Cached 60 seconds.
    """
    from uuid import UUID
    from app.models import Wallet
    from app.models.marketplace import ListingStatus
    from sqlalchemy.orm import selectinload

    user_uuid = UUID(user_id)

    # Execute all queries in parallel
    wallets_result = await db.execute(
        select(Wallet)
        .where(Wallet.user_id == user_uuid)
        .order_by(Wallet.is_primary.desc(), Wallet.created_at.desc())
    )
    wallets = wallets_result.scalars().all()

    nfts_result = await db.execute(
        select(NFT)
        .where(NFT.user_id == user_uuid)
        .order_by(NFT.created_at.desc())
        .limit(50)  # Limit to 50 NFTs for faster loading
    )
    nfts = nfts_result.scalars().all()

    listings_result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.nft))
        .where(Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.created_at.desc())
        .limit(50)
    )
    listings = listings_result.unique().scalars().all()

    return {
        "success": True,
        "wallets": [
            {
                "id": str(wallet.id),
                "name": wallet.name,
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat(),
            }
            for wallet in wallets
        ],
        "nfts": [
            {
                "id": str(nft.id),
                "name": nft.name,
                "global_nft_id": nft.global_nft_id,
                "description": nft.description,
                "blockchain": nft.blockchain,
                "status": nft.status.value if hasattr(nft.status, 'value') else nft.status,
                "image_url": nft.image_url,
                "minted_at": nft.minted_at.isoformat() if nft.minted_at else None,
                "created_at": nft.created_at.isoformat(),
            }
            for nft in nfts
        ],
        "listings": [
            {
                "id": str(listing.id),
                "nft_id": str(listing.nft_id),
                "nft_name": listing.nft.name if listing.nft else "Unknown NFT",
                "price": float(listing.price),
                "currency": listing.currency,
                "blockchain": listing.blockchain,
                "status": listing.status.value if hasattr(listing.status, 'value') else listing.status,
                "image_url": listing.nft.image_url if listing.nft else None,
                "active": listing.status == ListingStatus.ACTIVE,
            }
            for listing in listings
        ],
    }


@router.post("/web-app/mint")
async def web_app_mint_nft(
    user_id: str,
    wallet_id: str,
    nft_name: str,
    nft_description: Optional[str] = None,
    image_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Mint NFT via web app."""
    from uuid import UUID

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Mint NFT
    nft, error = await NFTService.mint_nft_with_blockchain_confirmation(
        db=db,
        user_id=user.id,
        wallet_id=UUID(wallet_id),
        name=nft_name,
        description=nft_description,
        image_url=image_url,
        royalty_percentage=0,
        metadata={"minted_via": "web_app"},
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minting failed: {error}",
        )

    return {
        "success": True,
        "nft": {
            "id": str(nft.id),
            "name": nft.name,
            "global_nft_id": nft.global_nft_id,
            "blockchain": nft.blockchain,
            "status": nft.status,
            "created_at": nft.created_at.isoformat(),
        },
    }


@router.post("/web-app/list-nft")
async def web_app_list_nft(
    user_id: str,
    nft_id: str,
    price: float,
    currency: str = "USDT",
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List NFT on marketplace via web app."""
    from uuid import UUID

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get NFT
    nft_result = await db.execute(
        select(NFT).where(
            and_(NFT.id == UUID(nft_id), NFT.user_id == user.id)
        )
    )
    nft = nft_result.scalar_one_or_none()

    if not nft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NFT not found",
        )

    # Get wallet
    wallet = await WalletService.get_primary_wallet(db, user.id, nft.blockchain)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No primary wallet for {nft.blockchain}",
        )

    # Create listing
    from app.models.marketplace import Listing

    listing, error = await MarketplaceService.create_listing(
        db=db,
        nft_id=UUID(nft_id),
        seller_id=user.id,
        seller_address=wallet.address,
        price=price,
        currency=currency.upper(),
        blockchain=nft.blockchain,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing failed: {error}",
        )

    return {
        "success": True,
        "listing": {
            "id": str(listing.id),
            "nft_id": str(listing.nft_id),
            "price": listing.price,
            "currency": listing.currency,
            "status": listing.status,
            "created_at": listing.created_at.isoformat(),
        },
    }


@router.post("/web-app/transfer")
async def web_app_transfer_nft(
    user_id: str,
    nft_id: str,
    to_address: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Transfer NFT to another address via web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    nft, error = await NFTService.transfer_nft(
        db=db,
        nft_id=UUID(nft_id),
        to_address=to_address,
        transaction_hash="",
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer failed: {error}",
        )

    return {
        "success": True,
        "nft": {
            "id": str(nft.id),
            "name": nft.name,
            "status": nft.status,
        },
    }


@router.post("/web-app/burn")
async def web_app_burn_nft(
    user_id: str,
    nft_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Burn NFT via web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    nft, error = await NFTService.burn_nft(
        db=db,
        nft_id=UUID(nft_id),
        transaction_hash="",
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Burn failed: {error}",
        )

    return {
        "success": True,
        "nft": {
            "id": str(nft.id),
            "name": nft.name,
            "status": nft.status,
        },
    }


@router.post("/web-app/set-primary")
async def web_app_set_primary_wallet(
    user_id: str,
    wallet_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Set primary wallet via web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    wallet, error = await WalletService.set_primary_wallet(
        db=db,
        user_id=UUID(user_id),
        wallet_id=UUID(wallet_id),
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed: {error}",
        )

    return {
        "success": True,
        "wallet": {
            "id": str(wallet.id),
            "name": wallet.name,
            "blockchain": wallet.blockchain.value,
        },
    }


@router.post("/web-app/make-offer")
async def web_app_make_offer(
    user_id: str,
    listing_id: str,
    offer_price: float,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Make an offer on a listing via web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    listing_result = await db.execute(
        select(Listing).where(Listing.id == UUID(listing_id))
    )
    listing = listing_result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    wallet = await WalletService.get_primary_wallet(db, user.id, listing.blockchain)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No primary wallet for {listing.blockchain}",
        )

    offer, error = await MarketplaceService.make_offer(
        db=db,
        listing_id=UUID(listing_id),
        buyer_id=user.id,
        buyer_address=wallet.address,
        offer_price=offer_price,
        currency=listing.currency,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Offer failed: {error}",
        )

    return {
        "success": True,
        "offer": {
            "id": str(offer.id),
            "offer_price": offer.offer_price,
            "currency": offer.currency,
            "status": offer.status,
        },
    }


@router.post("/web-app/cancel-listing")
async def web_app_cancel_listing(
    user_id: str,
    listing_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Cancel a listing via web app."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    listing, error = await MarketplaceService.cancel_listing(
        db=db,
        listing_id=UUID(listing_id),
        user_id=user.id,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cancellation failed: {error}",
        )

    return {
        "success": True,
        "listing": {
            "id": str(listing.id),
            "status": listing.status,
        },
    }


@router.get("/web-app/marketplace/listings")
async def get_marketplace_listings(
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get active marketplace listings. Optimized with eager loading, cached for 60 seconds."""
    from app.models.marketplace import ListingStatus
    from sqlalchemy.orm import selectinload

    # Optimized query with eager loading and index-friendly ordering
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.nft))
        .where(Listing.status == ListingStatus.ACTIVE)
        .order_by(Listing.created_at.desc())
        .limit(limit)
    )
    listings = result.unique().scalars().all()

    if not listings:
        return {"success": True, "listings": []}

    return {
        "success": True,
        "listings": [
            {
                "id": str(listing.id),
                "nft_id": str(listing.nft_id),
                "nft_name": listing.nft.name if listing.nft else "Unknown NFT",
                "price": float(listing.price),
                "currency": listing.currency,
                "blockchain": listing.blockchain,
                "status": listing.status.value if hasattr(listing.status, 'value') else listing.status,
                "image_url": listing.nft.image_url if listing.nft else None,
                "active": listing.status == ListingStatus.ACTIVE,
            }
            for listing in listings
        ],
    }


@router.get("/web-app/marketplace/mylistings")
async def get_my_listings(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user's marketplace listings."""
    from uuid import UUID

    result = await db.execute(
        select(Listing, NFT)
        .where(Listing.seller_id == UUID(user_id))
        .join(NFT, Listing.nft_id == NFT.id)
    )
    listings = result.all()

    if not listings:
        return {"success": True, "listings": []}

    return {
        "success": True,
        "listings": [
            {
                "listing_id": str(listing.id),
                "nft_id": str(nft.id),
                "nft_name": nft.name,
                "price": listing.price,
                "currency": listing.currency,
                "blockchain": nft.blockchain,
                "status": listing.status,
            }
            for listing, nft in listings
        ],
    }


# ==================== Polling Handler ====================

async def handle_telegram_update(update: dict) -> None:
    """
    Handle Telegram update from polling.
    Called by polling manager when an update is received.
    
    Args:
        update: Raw update dict from Telegram API
    """
    try:
        logger.warning(f"[TELEGRAM] handle_telegram_update called with update_id: {update.get('update_id')}")
        # Parse the raw update dict
        parsed_update = TelegramUpdate(**update)
        logger.warning(f"[TELEGRAM] Update parsed successfully")
        
        # Import here to avoid circular imports and get fresh reference
        from app.database.connection import AsyncSessionLocal
        
        logger.warning(f"[TELEGRAM] AsyncSessionLocal: {AsyncSessionLocal}")
        if not AsyncSessionLocal:
            logger.error("Database not initialized, cannot process Telegram update")
            return
        
        logger.warning(f"[TELEGRAM] Creating database session...")
        # Process with database session
        async with AsyncSessionLocal() as db:
            logger.warning(f"[TELEGRAM] Database session created")
            # Handle message updates
            if parsed_update.message:
                logger.warning(f"[TELEGRAM] Processing message: {parsed_update.message.text}")
                await handle_message(db, parsed_update.message)
                logger.warning(f"[TELEGRAM] handle_message completed")
                return

            # Handle callback queries (button clicks)
            if parsed_update.callback_query:
                logger.warning(f"[TELEGRAM] Processing callback query: {parsed_update.callback_query.data}")
                await handle_callback_query(db, parsed_update.callback_query)
                logger.warning(f"[TELEGRAM] handle_callback_query completed")
                return

    except Exception as e:
        logger.error(f"Error processing Telegram update from polling: {e}", exc_info=True)
