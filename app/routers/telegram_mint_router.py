import logging
import json
import anyio
import time
from typing import Optional
from urllib.parse import parse_qs
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db_session
from app.models import User, NFT
from app.models.marketplace import Listing
from app.models.wallet import BlockchainType
from app.schemas.wallet import CreateWalletRequest, ImportWalletRequest, WalletResponse
from app.schemas.nft import WebAppMintNFTRequest, WebAppListNFTRequest, WebAppTransferNFTRequest, WebAppBurnNFTRequest, WebAppSetPrimaryWalletRequest, WebAppMakeOfferRequest, WebAppCancelListingRequest
from app.services.telegram_bot_service import TelegramBotService
from app.services.nft_service import NFTService
from app.services.marketplace_service import MarketplaceService
from app.services.wallet_service import WalletService
from app.services.walletconnect_service import WalletConnectService
from app.services.telegram_dashboard_service import TelegramDashboardService
from app.utils.telegram_security import verify_telegram_data as verify_telegram_signature
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
async def get_telegram_user_from_request(request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
    init_data_str = request.query_params.get("init_data")
    logger.debug(f"get_telegram_user_from_request: initial init_data from query: {bool(init_data_str)}")
    if not init_data_str:
        try:
            body = getattr(request.state, 'body', None)
            if body is None:
                body = await request.body()
                request.state.body = body
            logger.debug(f"get_telegram_user_from_request: raw body length {len(body) if body else 0}")
            if body:
                body_dict = json.loads(body)
                init_data_str = body_dict.get("init_data")
                logger.debug(f"get_telegram_user_from_request: found init_data in body: {bool(init_data_str)}")
        except Exception as e:
            logger.debug(f"get_telegram_user_from_request: error reading body: {e}")
            pass
    if not init_data_str:
        logger.warning("No init_data provided - Telegram authentication required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram authentication required"
        )
    try:
        start_parse = time.time()
        params = parse_qs(init_data_str)
        data_dict = {key: value[0] if isinstance(value, list) else value for key, value in params.items()}
        logger.debug(f"get_telegram_user_from_request: parsed init_data keys={list(data_dict.keys())} parse_time={time.time()-start_parse:.3f}s")
    except Exception as e:
        logger.error(f"Failed to parse init_data: {e}")
        raise HTTPException(status_code=400, detail="Invalid init_data")
    if not verify_telegram_signature(data_dict):
        logger.warning(f"Signature verification failed for init_data - rejecting request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram signature - authentication failed"
        )
    user_data_str = data_dict.get("user")
    if not user_data_str:
        logger.error("No user data in init_data")
        raise HTTPException(status_code=400, detail="Missing user data in init_data")
    try:
        user_data = json.loads(user_data_str)
        telegram_id = user_data.get("id")
        if not telegram_id:
            raise ValueError("Missing telegram_id in user data")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse user data: {e}")
        raise HTTPException(status_code=400, detail="Invalid user data format")
    try:
        db_start = time.time()
        logger.debug(f"get_telegram_user_from_request: querying DB for telegram_id={telegram_id}")
        result = await db.execute(
            select(User).where(User.telegram_id == str(telegram_id))
        )
        user = result.scalar_one_or_none()
        logger.debug(f"get_telegram_user_from_request: db lookup time={time.time()-db_start:.3f}s, found_user={bool(user)}")
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    if not user:
        try:
            from app.services.auth_service import AuthService
            telegram_username = user_data.get("username", f"user_{telegram_id}")
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            logger.info(f"Creating Telegram user: id={telegram_id}, username={telegram_username}")
            user, error = await AuthService.authenticate_telegram(
                db=db,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
            )
            if error or not user:
                logger.error(f"Failed to create user: {error}")
                raise HTTPException(status_code=500, detail=f"Failed to create user: {error}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User creation error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create user")
    if not user.is_active:
        logger.error(f"User inactive: telegram_id={telegram_id}")
        raise HTTPException(status_code=403, detail="User account is inactive")
    logger.info(f"Authenticated user: telegram_id={telegram_id}, user_id={user.id}, username={user.username}")
    request.state.telegram_user = {
        "user_id": str(user.id),
        "telegram_id": user.telegram_id,
        "telegram_username": user.telegram_username,
        "user_obj": user,
        "authenticated": True,
    }
    logger.debug(f"Authenticated Telegram user: {telegram_id}")
    return request.state.telegram_user
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
    chat: dict
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
    wallet_id: str = Field(..., min_length=1)
    nft_name: str = Field(..., min_length=1, max_length=255)
    nft_description: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
@router.get("/webhook")
async def telegram_webhook_get(request: Request) -> dict:
    from app.config import get_settings
    settings = get_settings()
    if settings.environment.lower() == "production":
        logger.debug("GET request to webhook in production - returning 405")
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Method not allowed. Use POST to send Telegram updates."
        )
    logger.info(f"GET request to webhook from {request.client.host if request.client else 'unknown'} (development mode)")
    return {
        "status": "webhook_running",
        "environment": settings.environment,
        "webhook_url": settings.telegram_webhook_url,
        "message": "Webhook is running and ready to receive Telegram updates. Use POST method.",
        "debug_mode": True
    }
@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    try:
        from app.config import get_settings
        settings = get_settings()
        update_type = "message" if update.message else "callback_query" if update.callback_query else "unknown"
        logger.info(
            f"Telegram webhook: update_type={update_type} from IP={client_ip}"
        )
        if settings.telegram_webhook_secret:
            header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not header_secret:
                logger.warning(f"Webhook rejected: missing secret token header from {client_ip}")
                return {"ok": True, "error": "Missing secret token"}
            if header_secret != settings.telegram_webhook_secret:
                logger.warning(
                    f"Webhook rejected: secret token mismatch from {client_ip} "
                    f"(expected {len(settings.telegram_webhook_secret)} chars)"
                )
                return {"ok": True, "error": "Invalid secret token"}
        logger.debug(f"Webhook security: token validated ✓")
        if update.message:
            logger.info(
                f"Processing message: chat_id={update.message.chat.get('id')}, "
                f"user_id={update.message.get('from', {}).get('id')}"
            )
            await handle_message(db, update.message)
            logger.info(f"Message processed successfully")
        elif update.callback_query:
            logger.info(
                f"Processing callback: chat_id={update.callback_query.get('from', {}).get('id')}, "
                f"callback_data={update.callback_query.get('data', 'N/A')}"
            )
            await handle_callback_query(db, update.callback_query)
            logger.info(f"Callback processed successfully")
        else:
            logger.debug(f"Received Telegram update with no message or callback_query (update_id={update.update_id})")
        return {"ok": True}
    except HTTPException:
        logger.warning(f"Webhook validation error from {client_ip}: invalid update format")
        return {"ok": True}
    except Exception as e:
        logger.error(
            f"Webhook processing error from {client_ip}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        return {"ok": True}
async def handle_message(db: AsyncSession, message: TelegramMessage) -> None:
    chat_id = message.chat.get("id")
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = (message.text or "").strip()
    if not text:
        logger.debug(f"Empty message from {username} ({user_id}), skipping")
        return
    logger.info(f"Received message from {username} ({user_id}): {text}")
    user = await get_or_create_telegram_user(db, message.from_user)
    if not user:
        logger.error(f"Failed to create/get user for Telegram ID {user_id}")
        await bot_service.send_message(
            chat_id,
            "❌ Failed to authenticate. Please try again.",
        )
        return
    logger.debug(f"User authenticated: {user.id}")
    if hasattr(handle_admin_login, "_pending_admins") and chat_id in handle_admin_login._pending_admins:
        pending = handle_admin_login._pending_admins[chat_id]
        if pending.get("step") == "waiting_password":
            logger.info(f"Processing password input from {username}")
            await handle_admin_password_input(db, chat_id, user, text)
            return
    button_mapping = {
        "🚀 Get Started": "/dashboard",
        "📊 Dashboard": "/dashboard",
        "📋 Menu": "/menu",
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
        "🔄 Refresh": "/balance",
        "💰 Deposit USDT": "/deposit",
        "⚙️ Admin": "/admin-login",
        "🚪 Logout": "/admin-logout",
        "💰 Commission": "/admin-commission",
        "👥 Users": "/admin-users",
        "📊 Statistics": "/admin-stats",
        "💾 Backup": "/admin-backup",
        "📈 View Rate": "/admin-view-rate",
        "✏️ Edit Rate": "/admin-edit-rate",
        "🏪 View Wallets": "/admin-view-wallets",
        "🔄 Update Wallet": "/admin-update-wallet",
        "➕ Make Admin": "/admin-make-admin",
        "➖ Remove Admin": "/admin-remove-admin",
        "🚫 Suspend User": "/admin-suspend",
        "✅ Activate User": "/admin-activate",
        "📈 System Stats": "/admin-system-stats",
        "📋 Audit Logs": "/admin-audit-logs",
        "👨‍💼 Admin List": "/admin-list-admins",
        "💚 Health Check": "/admin-health-check",
        "📥 Export Backup": "/admin-export-backup",
        "🔧 Maintenance": "/admin-maintenance",
        "TON": "admin-blockchain:ton",
        "TRC20": "admin-blockchain:trc20",
        "ERC20": "admin-blockchain:erc20",
        "Solana": "admin-blockchain:solana",
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
        "🎨 Mint NFT": "/mint",
        "🎨 Start Minting": "/mint",
        "📤 Transfer": "/transfer",
        "🔥 Burn": "/burn",
        "🛍️ List for Sale": "/list",
        "🔍 Browse": "/browse",
        "❤️ Favorites": "/browse",
        "💬 Make Offer": "/offer",
        "📊 My Listings": "/mylistings",
        "❌ Cancel Listing": "/cancel-listing",
        "⟡ Ethereum": "blockchain:ethereum",
        "Ethereum": "blockchain:ethereum",
        "🔶 Polygon": "blockchain:polygon",
        "Polygon": "blockchain:polygon",
        "◎ Solana": "blockchain:solana",
        "Solana": "blockchain:solana",
        "💎 TON": "blockchain:ton",
        "₿ Bitcoin": "blockchain:bitcoin",
        "Bitcoin": "blockchain:bitcoin",
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
    if text in button_mapping:
        text = button_mapping[text]
    if text.startswith("blockchain:"):
        blockchain = text.split(":", 1)[1]
        logger.info(f"Detected blockchain selection from reply keyboard: {blockchain}")
        await handle_wallet_create_command(db, chat_id, user, blockchain)
        return
    if text == "/offer":
        await bot_service.send_message(chat_id, "To make an offer, reply with: /offer <listing_id> <amount>")
        return
        logger.info(f"Button pressed, converted to command: {text}")
    if text.startswith("/start"):
        logger.info(f"Processing /start command from {username}")
        await send_welcome_start(chat_id, username)
    elif text.startswith("/dashboard"):
        logger.info(f"Processing /dashboard command from {username}")
        await send_dashboard(db, chat_id, user, username)
    elif text.startswith("/balance"):
        logger.info(f"Processing /balance command from {username}")
        await send_balance(db, chat_id, user)
    elif text.startswith("/menu"):
        logger.info(f"Processing /menu command from {username}")
        await send_main_menu(chat_id, username)
    elif text.startswith("/quick-mint"):
        logger.info(f"Processing /quick-mint command from {username}")
        await send_quick_mint_screen(db, chat_id, user)
    elif text.startswith("/receive"):
        logger.info(f"Processing /receive command from {username}")
        await send_receive_menu(db, chat_id, user)
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
            logger.info(f"Calling handle_wallet_create_command with blockchain={blockchain}")
            await handle_wallet_create_command(db, chat_id, user, blockchain)
    elif text.startswith("/wallet"):
        await bot_service.send_wallet_list(db, chat_id, user.id)
    elif text.startswith("/wallets"):
        await bot_service.send_wallet_list(db, chat_id, user.id)
    elif text.startswith("/connect-wallet"):
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
    from app.config import get_settings
    logger.warning(f"[TELEGRAM] send_welcome_start called for chat_id={chat_id}, username={username}")
    settings = get_settings()
    message = (
        f"<b>🚀 Welcome to NFT Platform, {username}!</b>\n\n"
        f"<b>Your all-in-one platform for NFTs</b>\n\n"
        f"• Create & Manage Wallets\n"
        f"• Mint & Trade NFTs\n"
        f"• Multi-Blockchain Support\n\n"
        f"<b>Tap 'Open App' to get started</b> or use commands below:\n"
        f"• /wallets - Manage wallets\n"
        f"• /mint - Create NFTs\n"
        f"• /browse - Explore marketplace\n"
        f"• /mylistings - Your listings\n"
        f"• /dashboard - View stats"
    )
    keyboard = build_start_dashboard_inline(settings.telegram_webapp_url)
    logger.info("Sending /start dashboard with banner image and web_app button...")
    result = await bot_service.send_photo(
        chat_id, 
        settings.banner_image_url,
        caption=message,
        reply_markup=keyboard
    )
    logger.info(f"Welcome /start dashboard sent: {result}")
async def send_main_menu(chat_id: int, username: str) -> None:
    logger.warning(f"[TELEGRAM] send_main_menu called for chat_id={chat_id}, username={username}")
    message = (
        f"<b>🚀 Welcome to NFT Platform, {username}!</b>\n\n"
        f"Use the buttons below to navigate or type commands.\n\n"
        f"<b>What would you like to do?</b>"
    )
    logger.info("Calling bot_service.send_message with CTA menu keyboard...")
    result = await bot_service.send_message(
        chat_id, 
        message,
        reply_markup=build_dashboard_cta_keyboard()
    )
    logger.info(f"bot_service.send_message returned: {result}")
async def send_dashboard(db: AsyncSession, chat_id: int, user: User, username: str) -> None:
    logger.warning(f"[TELEGRAM] Sending dashboard for {username}")
    try:
        logger.warning(f"[DASHBOARD] Getting stats for user {user.id}")
        stats = await TelegramDashboardService.get_user_dashboard_stats(db, user.id)
        logger.warning(f"[DASHBOARD] Stats retrieved: {stats}")
        message = TelegramDashboardService.format_dashboard_message(username, stats)
        logger.warning(f"[DASHBOARD] Message formatted, sending with CTA keyboard")
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
    logger.warning(f"[TELEGRAM] Sending balance for user {user.id}")
    try:
        from app.models import Wallet
        from sqlalchemy import select
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
async def handle_admin_login(db: AsyncSession, chat_id: int, user: User) -> None:
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
    if not hasattr(handle_admin_login, "_pending_admins"):
        handle_admin_login._pending_admins = {}
    handle_admin_login._pending_admins[chat_id] = {"user_id": user.id, "username": user.username, "step": "waiting_password"}
async def handle_admin_password_input(db: AsyncSession, chat_id: int, user: User, password: str) -> None:
    logger.warning(f"[ADMIN] Password submission from user {user.id}")
    from app.config import settings
    from app.services.telegram_admin_service import TelegramAdminSession, TelegramAdminService
    if password != settings.admin_password:
        logger.warning(f"[ADMIN] Invalid password attempt from user {user.id}")
        await bot_service.send_message(
            chat_id,
            "❌ Invalid password. Access denied.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        if hasattr(handle_admin_login, "_pending_admins") and chat_id in handle_admin_login._pending_admins:
            del handle_admin_login._pending_admins[chat_id]
        return
    logger.warning(f"[ADMIN] Correct password, creating session for user {user.id}")
    TelegramAdminSession.create_session(chat_id, user.id, user.username)
    await handle_admin_dashboard(db, chat_id, user)
async def handle_admin_logout(chat_id: int, user: User) -> None:
    logger.warning(f"[ADMIN] Admin logout for user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession
    TelegramAdminSession.logout(chat_id)
    await bot_service.send_message(
        chat_id,
        "✅ Logged out from admin panel.",
        reply_markup=build_dashboard_cta_keyboard()
    )
async def handle_admin_dashboard(db: AsyncSession, chat_id: int, user: User) -> None:
    logger.warning(f"[ADMIN] Dashboard access by user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession, TelegramAdminService
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        logger.warning(f"[ADMIN] User {user.id} not logged in for dashboard")
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel. Please use /admin-login",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
    dashboard_msg = TelegramAdminService.format_admin_dashboard()
    await bot_service.send_message(
        chat_id,
        dashboard_msg,
        reply_markup=build_admin_dashboard_keyboard()
    )
async def handle_admin_commission(db: AsyncSession, chat_id: int, user: User) -> None:
    logger.warning(f"[ADMIN] Commission menu for user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.config import settings
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
    logger.warning(f"[ADMIN] User management menu for user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.models import User as UserModel
    from sqlalchemy import select
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
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
    logger.warning(f"[ADMIN] Statistics menu for user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession
    from app.models import User as UserModel, NFT, Wallet
    from sqlalchemy import select, func
    if not TelegramAdminSession.is_admin_logged_in(chat_id):
        await bot_service.send_message(
            chat_id,
            "❌ You are not logged in to admin panel.",
            reply_markup=build_dashboard_cta_keyboard()
        )
        return
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
    logger.warning(f"[ADMIN] Backup menu for user {user.id}")
    from app.services.telegram_admin_service import TelegramAdminSession
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
    await bot_service.send_message(
        chat_id,
        "⏳ Processing your mint request...",
    )
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
    supported_blockchains = ["ethereum", "solana", "polygon", "bitcoin", "ton"]
    if blockchain.lower() not in supported_blockchains:
        await bot_service.send_message(
            chat_id,
            f"❌ Unsupported blockchain: {blockchain}\n\n"
            f"Supported: {', '.join(supported_blockchains)}",
        )
        return
    try:
        uri = WalletConnectService.generate_connection_uri()
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
    logger.warning(f"[HANDLER] handle_wallet_create_command called: user_id={user.id}, blockchain={blockchain}")
    await bot_service.send_message(chat_id, f"⏳ Creating {blockchain.upper()} wallet...")
    logger.warning(f"[HANDLER] Sent 'Creating wallet' message")
    wallet, error = await bot_service.handle_wallet_create(
        db=db, chat_id=chat_id, user=user, blockchain=blockchain
    )
    logger.warning(f"[HANDLER] handle_wallet_create returned: wallet={wallet is not None}, error={error}")
    if wallet:
        logger.info(f"✓ Wallet created successfully: {wallet.id}")
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
    chat_id = callback.message.chat.get("id") if callback.message else None
    user_id = callback.from_user.id
    data = callback.data or ""
    logger.info(f"Callback query from {user_id}: {data}")
    user = await get_or_create_telegram_user(db, callback.from_user)
    if not user:
        return
    if data.startswith("mint_wallet_"):
        wallet_id = data.replace("mint_wallet_", "")
        await bot_service.send_message(
            chat_id,
            f"Selected wallet: <code>{wallet_id[:10]}...</code>\n"
            f"Please reply with the NFT name and details:\n"
            f"/mint {wallet_id} &lt;name&gt;",
        )
    elif data.startswith("wallet_info_"):
        wallet_id = data.replace("wallet_info_", "")
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
        await bot_service.send_message(
            chat_id,
            "To create a wallet, choose a blockchain or use the command:\n/wallet-create <blockchain>",
            reply_markup=build_blockchain_cta_keyboard(),
        )
    elif data.startswith("select_blockchain:"):
        blockchain = data.split(":", 1)[1]
        await handle_wallet_create_command(db, chat_id, user, blockchain)
    elif data == "admin_dashboard":
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.telegram_id == str(callback.from_user.id)))
        user = result.scalar_one_or_none()
        if not user:
            return
        if getattr(user, 'user_role', None) and str(user.user_role).upper().endswith('ADMIN'):
            from app.utils.telegram_keyboards import build_admin_dashboard_inline
            await bot_service.send_message(chat_id, "Opening admin dashboard...", reply_markup=build_admin_dashboard_inline())
        else:
            await bot_service.send_message(chat_id, "❌ You are not authorized for admin actions.")
    elif data.startswith("/"):
        cmd = data
        try:
            if cmd == "/wallets" or cmd == "/wallet":
                await bot_service.send_wallet_list(db, chat_id, user.id)
            elif cmd == "/balance":
                await send_balance(db, chat_id, user)
            elif cmd == "/quick-mint":
                await send_quick_mint_screen(db, chat_id, user)
            elif cmd == "/transfer":
                await handle_transfer_command(db, chat_id, user, cmd)
            elif cmd == "/mynfts":
                await bot_service.send_user_nfts(db, chat_id, user.id)
            elif cmd == "/browse":
                await bot_service.send_marketplace_listings(db, chat_id)
            elif cmd == "/mylistings":
                await bot_service.send_user_listings(db, chat_id, user.id)
            elif cmd == "/wallet-create":
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
                await bot_service.send_message(
                    chat_id,
                    "To deposit USDT, send funds to your primary wallet address or use the on-ramp services listed in the app dashboard.",
                )
            elif cmd == "/help":
                await bot_service.send_message(chat_id, "Send /start to see available commands or visit the help page.")
        except Exception as e:
            logger.error(f"Error handling inline command callback {cmd}: {e}")
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
        await bot_service.send_message(
            chat_id,
            f"To make an offer for listing <code>{listing_id}</code>, reply with:\n/offer {listing_id} <amount>",
        )
async def get_or_create_telegram_user(
    db: AsyncSession, telegram_user: TelegramUser
) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.telegram_id == str(telegram_user.id))
    )
    user = result.scalar_one_or_none()
    if user:
        return user
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
@router.post("/webhook/set")
async def set_webhook(webhook_url: str) -> dict:
    from app.config import get_settings
    settings = get_settings()
    secret = settings.telegram_webhook_secret if getattr(settings, "telegram_webhook_secret", None) else None
    success = await bot_service.set_webhook(webhook_url, secret_token=secret)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set webhook",
        )
    return {
        "success": True,
        "message": f"Webhook set to {webhook_url}",
    }
@router.post("/webhook/delete")
async def delete_webhook() -> dict:
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
@router.get("/webhook/info")
async def webhook_info() -> dict:
    try:
        from app.config import get_settings
        settings = get_settings()
        info = await bot_service.get_webhook_info()
        return {
            "status": "ok",
            "webhook_url": settings.telegram_webhook_url,
            "webhook_secret": "***configured***" if settings.telegram_webhook_secret else "not configured",
            "auto_setup_enabled": settings.telegram_auto_setup_webhook,
            "telegram_webhook_info": info or {"status": "not configured"},
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting webhook info: {str(e)}"
        )
@router.post("/send-notification")
async def send_telegram_notification(
    user_id: str,
    title: str,
    message: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
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
@router.get("/webapp/init")
async def web_app_init(
    init_data: str = None,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        if not init_data:
            logger.error("No init_data provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Telegram authentication required - please open from Telegram bot",
            )
        logger.debug(f"WebApp init: received init_data (length={len(init_data)})")
        try:
            params = parse_qs(init_data)
            data_dict = {key: value[0] if isinstance(value, list) else value for key, value in params.items()}
            logger.debug(f"Parsed init_data keys: {list(data_dict.keys())}")
        except Exception as e:
            logger.error(f"Failed to parse init_data: {e}")
            raise HTTPException(status_code=400, detail="Invalid init_data format")
        if not verify_telegram_signature(data_dict):
            logger.warning(f"Signature verification failed - continuing anyway")
        user_data_json = data_dict.get("user")
        if not user_data_json:
            logger.error("No user data in init_data")
            raise HTTPException(status_code=400, detail="Missing user data in init_data")
        try:
            user_data = json.loads(user_data_json)
            telegram_id = user_data.get("id")
            if not telegram_id:
                raise ValueError("Missing telegram_id")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse user data: {e}")
            raise HTTPException(status_code=400, detail="Invalid user data")
        try:
            result = await db.execute(
                select(User).where(User.telegram_id == str(telegram_id))
            )
            user = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        if not user:
            try:
                from app.services.auth_service import AuthService
                telegram_username = user_data.get("username", f"user_{telegram_id}")
                first_name = user_data.get("first_name", "")
                last_name = user_data.get("last_name", "")
                logger.info(f"Creating Telegram user: id={telegram_id}, username={telegram_username}")
                user, error = await AuthService.authenticate_telegram(
                    db=db,
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                    first_name=first_name,
                    last_name=last_name,
                )
                if error or not user:
                    logger.error(f"Failed to create user: {error}")
                    raise HTTPException(status_code=500, detail=f"Failed to create user")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"User creation error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to create user")
        if not user.is_active:
            logger.error(f"User inactive: telegram_id={telegram_id}")
            raise HTTPException(status_code=403, detail="User account is inactive")
        logger.info(f"User authenticated: id={user.id}, telegram_id={user.telegram_id}")
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "telegram_id": user.telegram_id,
                "telegram_username": user.telegram_username or "User",
                "full_name": user.full_name or user.telegram_username or "User",
                "avatar_url": user.avatar_url,
                "email": user.email,
                "is_verified": user.is_verified,
                "user_role": user.user_role.value if hasattr(user.user_role, 'value') else str(user.user_role),
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WebApp init error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Initialization failed",
        )
@router.get("/webapp/user")
async def web_app_get_user(
    user_id: str,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    from uuid import UUID
    if not telegram_user.get("authenticated"):
        logger.warning(f"Unauthenticated user attempted to access /webapp/user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access user data",
        )
    if str(telegram_user["user_id"]) != user_id:
        logger.warning(f"User ID mismatch: session={telegram_user['user_id']}, requested={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: user_id mismatch",
        )
    user = telegram_user["user_obj"]
    logger.info(f"User data accessed: telegram_id={telegram_user['telegram_id']}, user_id={user_id}")
    return {
        "success": True,
        "user": {
            "id": str(user.id),
            "telegram_id": user.telegram_id,
            "telegram_username": user.telegram_username,
            "full_name": user.full_name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
        },
    }
@router.get("/webapp/wallets")
async def web_app_get_wallets(
    user_id: str,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    from uuid import UUID
    from app.models import Wallet
    if str(telegram_user["user_id"]) != user_id:
        logger.warning(f"User ID mismatch in wallets: session={telegram_user['user_id']}, requested={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: user_id mismatch",
        )
    logger.info(f"Wallets accessed: telegram_id={telegram_user['telegram_id']}, user_id={user_id}")
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
                "blockchain": wallet.blockchain.value,
                "address": wallet.address,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat(),
            }
            for wallet in wallets
        ],
    }
    return response_data
@router.get("/webapp/nfts")
async def web_app_get_user_nfts(
    user_id: str,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    from uuid import UUID
    if not telegram_user.get("authenticated"):
        logger.warning(f"Unauthenticated user attempted to access /webapp/nfts")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access NFT data",
        )
    if str(telegram_user["user_id"]) != user_id:
        logger.warning(f"User ID mismatch in NFTs: session={telegram_user['user_id']}, requested={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: user_id mismatch",
        )
    logger.info(f"NFTs accessed: telegram_id={telegram_user['telegram_id']}, user_id={user_id}")
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
@router.get("/webapp/dashboard-data")
async def web_app_get_dashboard_data(
    user_id: str,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        from uuid import UUID
        from app.models import Wallet
        from app.models.marketplace import ListingStatus
        from sqlalchemy.orm import selectinload
        if str(telegram_user["user_id"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: user_id mismatch",
            )
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user_id format: {user_id}"
            )
        try:
            wallets_result = await db.execute(
                select(Wallet)
                .where(Wallet.user_id == user_uuid)
                .order_by(Wallet.is_primary.desc(), Wallet.created_at.desc())
            )
            wallets = wallets_result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to fetch wallets: {str(e)}")
            wallets = []
        try:
            nfts_result = await db.execute(
                select(NFT)
                .where(NFT.user_id == user_uuid)
                .order_by(NFT.created_at.desc())
                .limit(50)
            )
            nfts = nfts_result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to fetch NFTs: {str(e)}")
            nfts = []
        try:
            listings_result = await db.execute(
                select(Listing)
                .options(selectinload(Listing.nft))
                .where((Listing.seller_id == user_uuid) & (Listing.status == ListingStatus.ACTIVE))
                .order_by(Listing.created_at.desc())
                .limit(50)
            )
            listings = listings_result.unique().scalars().all()
        except Exception as e:
            logger.error(f"Failed to fetch listings: {str(e)}")
            listings = []
        return {
            "success": True,
            "wallets": [
                {
                    "id": str(wallet.id),
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard data fetch error: {str(e)}", exc_info=True)
        return {
            "success": True,
            "wallets": [],
            "nfts": [],
            "listings": [],
            "error": f"Partial data load: {str(e)}"
        }
@router.post("/webapp/mint")
async def web_app_mint_nft(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    from app.models import Wallet
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[MINT_NFT] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[MINT_NFT] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppMintNFTRequest(**body_data)
        except Exception as e:
            logger.error(f"[MINT_NFT] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        try:
            wallet_result = await db.execute(
                select(Wallet).where(
                    and_(Wallet.id == request.wallet_id, Wallet.user_id == user.id)
                )
            )
            wallet = wallet_result.scalar_one_or_none()
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet not found or does not belong to user",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Wallet lookup error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate wallet",
            )
        nft, error = await NFTService.mint_nft_with_blockchain_confirmation(
            db=db,
            user_id=user.id,
            wallet_id=request.wallet_id,
            name=request.nft_name,
            description=request.nft_description,
            image_url=request.image_url,
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
                "description": nft.description,
                "status": nft.status.value if hasattr(nft.status, 'value') else str(nft.status),
                "image_url": nft.image_url,
                "owner_address": nft.owner_address,
                "is_locked": nft.is_locked,
                "created_at": nft.created_at.isoformat(),
                "minted_at": nft.minted_at.isoformat() if nft.minted_at else None,
            },
        }
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during mint operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mint error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mint operation failed: {str(e)}")
@router.post("/webapp/list-nft")
async def web_app_list_nft(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body_data = await http_request.json()
            request = WebAppListNFTRequest(**body_data)
        except Exception as e:
            logger.error(f"Failed to parse request: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        nft_result = await db.execute(
            select(NFT).where(
                and_(NFT.id == request.nft_id, NFT.user_id == user.id)
            )
        )
        nft = nft_result.scalar_one_or_none()
        if not nft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NFT not found",
            )
        wallet = await WalletService.get_primary_wallet(db, user.id, nft.blockchain)
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No primary wallet for {nft.blockchain}",
            )
        from app.models.marketplace import Listing
        listing, error = await MarketplaceService.create_listing(
            db=db,
            nft_id=request.nft_id,
            seller_id=user.id,
            seller_address=wallet.address,
            price=request.price,
            currency=request.currency.upper(),
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during list operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="List operation failed")
@router.post("/webapp/transfer")
async def web_app_transfer_nft(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[TRANSFER_NFT] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[TRANSFER_NFT] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppTransferNFTRequest(**body_data)
        except Exception as e:
            logger.error(f"[TRANSFER_NFT] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        nft, error = await NFTService.transfer_nft(
            db=db,
            nft_id=request.nft_id,
            to_address=request.to_address,
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during transfer operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transfer error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transfer operation failed")
@router.post("/webapp/burn")
async def web_app_burn_nft(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[BURN_NFT] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[BURN_NFT] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppBurnNFTRequest(**body_data)
        except Exception as e:
            logger.error(f"[BURN_NFT] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        nft, error = await NFTService.burn_nft(
            db=db,
            nft_id=request.nft_id,
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during burn operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Burn error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Burn operation failed")
@router.post("/webapp/set-primary")
async def web_app_set_primary_wallet(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[SET_PRIMARY] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[SET_PRIMARY] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppSetPrimaryWalletRequest(**body_data)
        except Exception as e:
            logger.error(f"[SET_PRIMARY] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        wallet, error = await WalletService.set_primary_wallet(
            db=db,
            user_id=user.id,
            wallet_id=request.wallet_id,
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during set-primary operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set-primary error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Operation failed")
@router.post("/webapp/make-offer")
async def web_app_make_offer(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[MAKE_OFFER] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[MAKE_OFFER] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppMakeOfferRequest(**body_data)
        except Exception as e:
            logger.error(f"[MAKE_OFFER] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        listing_result = await db.execute(
            select(Listing).where(Listing.id == request.listing_id)
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
            listing_id=request.listing_id,
            buyer_id=user.id,
            buyer_address=wallet.address,
            offer_price=request.offer_price,
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during make-offer operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Make-offer error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Offer operation failed")
@router.post("/webapp/cancel-listing")
async def web_app_cancel_listing(
    http_request: Request,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    import anyio
    from uuid import UUID
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[CANCEL_LISTING] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[CANCEL_LISTING] No cached body, reading from stream")
                body_data = await http_request.json()
            request = WebAppCancelListingRequest(**body_data)
        except Exception as e:
            logger.error(f"[CANCEL_LISTING] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if str(request.user_id) != telegram_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id mismatch",
            )
        user = telegram_user["user_obj"]
        listing, error = await MarketplaceService.cancel_listing(
            db=db,
            listing_id=request.listing_id,
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
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during cancel-listing operation")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel-listing error: {e}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cancellation failed")
@router.get("/webapp/marketplace/listings")
async def get_marketplace_listings(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        from app.models.marketplace import ListingStatus
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Listing)
            .options(
                selectinload(Listing.nft),
                selectinload(Listing.seller)
            )
            .where(Listing.status == ListingStatus.ACTIVE)
            .order_by(Listing.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        listings_db = result.scalars().unique().all()
        if not listings_db:
            return {"success": True, "listings": []}
        listings = []
        for listing in listings_db:
            try:
                nft = listing.nft
                seller = listing.seller
                listings.append({
                    "id": str(listing.id),
                    "nft_id": str(listing.nft_id),
                    "nft_name": nft.name if nft else "Unknown NFT",
                    "price": float(listing.price),
                    "currency": listing.currency,
                    "blockchain": listing.blockchain,
                    "status": listing.status.value if hasattr(listing.status, 'value') else str(listing.status),
                    "image_url": nft.image_url if nft else None,
                    "active": listing.status == ListingStatus.ACTIVE,
                    "seller_id": str(listing.seller_id) if listing.seller_id else None,
                    "seller_name": seller.telegram_username or seller.full_name or "Anonymous" if seller else "Anonymous",
                })
            except Exception as e:
                logger.error(f"Error processing listing {listing.id}: {e}")
                continue
        return {
            "success": True,
            "listings": listings,
        }
    except Exception as e:
        logger.error(f"Marketplace listings error: {e}", exc_info=True)
        return {
            "success": False,
            "listings": [],
            "error": str(e),
        }
@router.get("/webapp/marketplace/mylistings")
async def get_my_listings(
    user_id: str,
    telegram_user: dict = Depends(get_telegram_user_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    from uuid import UUID
    if str(telegram_user["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: user_id mismatch",
        )
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
@router.post("/webapp/create-wallet", response_model=dict)
async def create_wallet_for_webapp(
    http_request: Request,
    db: AsyncSession = Depends(get_db_session),
    auth: dict = Depends(get_telegram_user_from_request),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    import anyio
    from app.services.activity_service import ActivityService
    from app.models.activity import ActivityType
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[CREATE_WALLET] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[CREATE_WALLET] No cached body, reading from stream")
                body_data = await http_request.json()
            logger.info(f"[CREATE_WALLET] Request body: {body_data}")
            request = CreateWalletRequest(**body_data)
        except Exception as e:
            logger.error(f"Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if not auth or not isinstance(auth, dict):
            logger.error(f"[CREATE_WALLET] Auth invalid: auth={auth}, type={type(auth)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        user_id = auth.get("user_id")
        user = auth.get("user_obj")
        logger.info(f"[CREATE_WALLET] Auth check: user_id={user_id}, user={user}")
        if not user_id or not user:
            logger.error(f"[CREATE_WALLET] Missing user data: user_id={user_id}, user_obj={user}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication data",
            )
        telegram_username = user.telegram_username
        telegram_id = user.telegram_id
        chat_id = telegram_id
        logger.info(f"[CREATE_WALLET] User verified: telegram_id={telegram_id}, username={telegram_username}")
        if not request or not request.blockchain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="blockchain is required in request body",
            )
        blockchain_value = str(request.blockchain).lower() if request.blockchain else None
        valid_blockchains = ['bitcoin', 'ethereum', 'solana', 'ton', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche']
        if blockchain_value not in valid_blockchains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {blockchain_value}. Must be one of: {', '.join(valid_blockchains)}",
            )
        logger.info(f"[CREATE_WALLET] START: user={user_id}, blockchain={blockchain_value}")
        wallet = None
        error = None
        try:
            blockchain_type = BlockchainType(blockchain_value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {blockchain_value}",
            )
        gen_start = time.time()
        wallet = None
        error = None
        try:
            async def generate_wallet():
                try:
                    logger.debug(f"[CREATE_WALLET] Generating {blockchain_type} wallet for user {user.id}")
                    if blockchain_type in (BlockchainType.ETHEREUM, BlockchainType.POLYGON, 
                                           BlockchainType.ARBITRUM, BlockchainType.OPTIMISM,
                                           BlockchainType.BASE, BlockchainType.AVALANCHE):
                        logger.debug(f"[CREATE_WALLET] Calling generate_evm_wallet for {blockchain_type}")
                        result = await WalletService.generate_evm_wallet(db=db, user_id=user.id, blockchain=blockchain_type, make_primary=True)
                        logger.debug(f"[CREATE_WALLET] EVM wallet gen result: {result}")
                        return result
                    elif blockchain_type == BlockchainType.TON:
                        logger.debug("[CREATE_WALLET] Calling generate_ton_wallet")
                        result = await WalletService.generate_ton_wallet(db=db, user_id=user.id, blockchain=BlockchainType.TON, make_primary=True)
                        logger.debug(f"[CREATE_WALLET] TON wallet gen result: {result}")
                        return result
                    elif blockchain_type == BlockchainType.SOLANA:
                        logger.debug("[CREATE_WALLET] Calling generate_solana_wallet")
                        result = await WalletService.generate_solana_wallet(db=db, user_id=user.id, blockchain=BlockchainType.SOLANA, make_primary=True)
                        logger.debug(f"[CREATE_WALLET] Solana wallet gen result: {result}")
                        return result
                    elif blockchain_type == BlockchainType.BITCOIN:
                        logger.debug("[CREATE_WALLET] Calling generate_bitcoin_wallet")
                        result = await WalletService.generate_bitcoin_wallet(db=db, user_id=user.id, blockchain=BlockchainType.BITCOIN, make_primary=True)
                        logger.debug(f"[CREATE_WALLET] Bitcoin wallet gen result: {result}")
                        return result
                    else:
                        logger.error(f"[CREATE_WALLET] Unsupported blockchain: {blockchain_value}")
                        return None, f"Unsupported blockchain: {blockchain_value}"
                except Exception as e:
                    logger.error(f"[CREATE_WALLET] Error in generate_wallet: {e}", exc_info=True)
                    raise
            import asyncio
            try:
                result = await asyncio.wait_for(generate_wallet(), timeout=30.0)
                if isinstance(result, tuple) and len(result) == 2:
                    wallet, error = result
                else:
                    logger.error(f"[CREATE_WALLET] Invalid result format from wallet generation: {result}")
                    error = "Invalid wallet generation result"
            except asyncio.TimeoutError:
                logger.error(f"[CREATE_WALLET] TIMEOUT: Wallet generation took >30s for {blockchain_value}")
                error = f"Wallet generation timeout - blockchain RPC may be unresponsive"
        except Exception as e:
            logger.error(f"[CREATE_WALLET] Exception in wallet generation: {e}", exc_info=True)
            error = str(e)
        finally:
            logger.debug(f"[CREATE_WALLET] Wallet generation finished (time={time.time()-gen_start:.3f}s)")
        if error or not wallet:
            logger.error(f"[CREATE_WALLET] FAILED: {error}")
            try:
                await ActivityService.log_error(
                    db=db,
                    user_id=user.id,
                    activity_type=ActivityType.WALLET_CREATED,
                    error_message=error or "Unknown error",
                    resource_type="wallet",
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to log error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create wallet: {error or 'Unknown error'}",
            )
        logger.info(f"[CREATE_WALLET] SUCCESS: wallet_id={wallet.id}")
        try:
            logger.debug(f"[CREATE_WALLET] Logging activity for wallet {wallet.id}")
            await ActivityService.log_wallet_created(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                blockchain=blockchain_value,
                address=wallet.address,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
            )
            logger.debug("[CREATE_WALLET] Activity logged, committing db")
            await db.commit()
            logger.debug("[CREATE_WALLET] Activity commit successful")
        except Exception as e:
            logger.error(f"[CREATE_WALLET] Failed to log activity: {e}", exc_info=True)
        logger.debug(f"[CREATE_WALLET] Returning wallet response: {wallet.blockchain.value}, {wallet.address}")
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "blockchain": wallet.blockchain.value if hasattr(wallet.blockchain, 'value') else str(wallet.blockchain),
                "address": wallet.address,
                "wallet_type": wallet.wallet_type.value if hasattr(wallet.wallet_type, 'value') else str(wallet.wallet_type),
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            },
        }
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during create-wallet")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        logger.debug(f"HTTPException raised in create-wallet, re-raising")
        raise
    except Exception as e:
        logger.error(f"[CREATE_WALLET] FATAL ERROR: {type(e).__name__}: {e}", exc_info=True)
        import traceback
        logger.error(f"[CREATE_WALLET] Stack trace:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wallet: {str(e)}",
        )
@router.post("/webapp/import-wallet", response_model=dict)
async def import_wallet_for_webapp(
    http_request: Request,
    db: AsyncSession = Depends(get_db_session),
    auth: dict = Depends(get_telegram_user_from_request),
) -> dict:
    import anyio
    from app.services.activity_service import ActivityService
    from app.models.activity import ActivityType
    try:
        try:
            body = getattr(http_request.state, 'body', None)
            if body:
                logger.debug(f"[IMPORT_WALLET] Using cached body (length={len(body)})")
                body_data = json.loads(body)
            else:
                logger.debug("[IMPORT_WALLET] No cached body, reading from stream")
                body_data = await http_request.json()
            logger.info(f"[IMPORT_WALLET] Request body: {body_data}")
            request = ImportWalletRequest(**body_data)
        except Exception as e:
            logger.error(f"[IMPORT_WALLET] Failed to parse request: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request body: {str(e)}"
            )
        if not auth or not isinstance(auth, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        user_id = auth.get("user_id")
        user = auth.get("user_obj")
        if not user_id or not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication data",
            )
        telegram_username = user.telegram_username
        telegram_id = user.telegram_id
        if not request or not request.blockchain or not request.address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="blockchain and address are required in request body",
            )
        blockchain_value = str(request.blockchain).lower() if request.blockchain else None
        valid_blockchains = ['bitcoin', 'ethereum', 'solana', 'ton', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche']
        if blockchain_value not in valid_blockchains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid blockchain: {blockchain_value}. Valid options are: {', '.join(valid_blockchains)}"
            )
        wallet, error = await WalletService.import_wallet(
            db=db,
            user_id=user.id,
            blockchain=BlockchainType(blockchain_value),
            address=request.address,
            public_key=request.public_key,
            is_primary=request.is_primary if hasattr(request, 'is_primary') else False,
        )
        if error:
            logger.error(f"Wallet import error: {error}")
            try:
                await ActivityService.log_error(
                    db=db,
                    user_id=user.id,
                    activity_type=ActivityType.WALLET_IMPORTED,
                    error_message=error,
                    resource_type="wallet",
                    metadata={"blockchain": blockchain_value, "address": request.address},
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to log error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import wallet: {error}",
            )
        try:
            await ActivityService.log_wallet_imported(
                db=db,
                user_id=user.id,
                wallet_id=wallet.id,
                blockchain=blockchain_value,
                address=request.address,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
        logger.info(f"Wallet imported for user {telegram_username}: {wallet.id}")
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "name": wallet.name if hasattr(wallet, 'name') else f"Imported {blockchain_value}",
                "blockchain": wallet.blockchain.value if hasattr(wallet.blockchain, 'value') else str(wallet.blockchain),
                "address": wallet.address,
                "is_primary": wallet.is_primary,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            },
        }
    except (anyio.EndOfStream, anyio.WouldBlock):
        logger.debug("Client disconnected during import-wallet")
        return {"success": False, "detail": "Client disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import wallet error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import wallet: {str(e)}",
        )
async def handle_telegram_update(update: dict) -> None:
    try:
        logger.warning(f"[TELEGRAM] handle_telegram_update called with update_id: {update.get('update_id')}")
        parsed_update = TelegramUpdate(**update)
        logger.warning(f"[TELEGRAM] Update parsed successfully")
        from app.database.connection import AsyncSessionLocal
        logger.warning(f"[TELEGRAM] AsyncSessionLocal: {AsyncSessionLocal}")
        if not AsyncSessionLocal:
            logger.error("Database not initialized, cannot process Telegram update")
            return
        logger.warning(f"[TELEGRAM] Creating database session...")
        async with AsyncSessionLocal() as db:
            logger.warning(f"[TELEGRAM] Database session created")
            if parsed_update.message:
                logger.warning(f"[TELEGRAM] Processing message: {parsed_update.message.text}")
                await handle_message(db, parsed_update.message)
                logger.warning(f"[TELEGRAM] handle_message completed")
                return
            if parsed_update.callback_query:
                logger.warning(f"[TELEGRAM] Processing callback query: {parsed_update.callback_query.data}")
                await handle_callback_query(db, parsed_update.callback_query)
                logger.warning(f"[TELEGRAM] handle_callback_query completed")
                return
    except Exception as e:
        logger.error(f"Error processing Telegram update from polling: {e}", exc_info=True)
