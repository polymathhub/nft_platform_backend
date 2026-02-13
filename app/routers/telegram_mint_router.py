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
from app.utils.telegram_security import verify_telegram_data

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

    # Parse command
    if text.startswith("/start"):
        logger.warning(f"[TELEGRAM] Processing /start command from {username}")
        await send_main_menu(chat_id, username)

    elif text.startswith("/wallet"):
        await bot_service.send_wallet_list(db, chat_id, user.id)

    elif text.startswith("/wallets"):
        await bot_service.send_wallet_list(db, chat_id, user.id)

    elif text.startswith("/wallet-create"):
        parts = text.split()
        if len(parts) < 2:
            await bot_service.send_wallet_creation_guide(chat_id)
        else:
            blockchain = parts[1].lower()
            await handle_wallet_create_command(db, chat_id, user, blockchain)

    elif text.startswith("/wallet-import"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await bot_service.send_wallet_creation_guide(chat_id)
        else:
            blockchain = parts[1].lower()
            address = parts[2]
            await handle_wallet_import_command(db, chat_id, user, blockchain, address)

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

    elif text.startswith("/help"):
        await send_help_message(chat_id)

    else:
        await bot_service.send_message(
            chat_id,
            "Unknown command. Use /help to see available commands.",
        )


async def send_main_menu(chat_id: int, username: str) -> None:
    logger.warning(f"[TELEGRAM] send_main_menu called for chat_id={chat_id}, username={username}")
    message = (
        f"<b>Welcome to NFT Platform, {username}! 🚀</b>\n\n"
        f"<b>📌 Main Menu:</b>\n\n"
        f"<b>NFT Operations:</b>\n"
        f"• <code>/mint</code> - Mint new NFT (with image URL)\n"
        f"• <code>/mynfts</code> - View your NFTs\n"
        f"• <code>/status &lt;id&gt;</code> - Check NFT status\n\n"
        f"<b>Marketplace:</b>\n"
        f"• <code>/browse</code> - Browse listings\n"
        f"• <code>/list &lt;nft_id&gt; &lt;price&gt;</code> - List NFT\n"
        f"• <code>/mylistings</code> - Your listings\n"
        f"• <code>/offer &lt;listing_id&gt; &lt;price&gt;</code> - Make offer\n\n"
        f"<b>Wallet:</b>\n"
        f"• <code>/wallets</code> - List wallets\n"
        f"• <code>/set-primary &lt;id&gt;</code> - Set primary wallet\n\n"
        f"<b>More:</b>\n"
        f"• <code>/help</code> - Full command list\n"
    )
    logger.warning(f"[TELEGRAM] Calling bot_service.send_message...")
    result = await bot_service.send_message(chat_id, message)
    logger.warning(f"[TELEGRAM] bot_service.send_message returned: {result}")


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
    logger.info(f"[WALLET] Creating wallet for user {user.id}, blockchain: {blockchain}")
    
    await bot_service.send_message(chat_id, f"⏳ Creating {blockchain.upper()} wallet...")
    
    wallet, error = await bot_service.handle_wallet_create(
        db=db, chat_id=chat_id, user=user, blockchain=blockchain
    )
    
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

@router.post("/webhook")
async def telegram_webhook(update: dict):
    # handle Telegram update
    return {"status": "ok"}
    
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
    """Get user's wallets for web app."""
    from uuid import UUID
    from app.models import Wallet

    result = await db.execute(
        select(Wallet).where(Wallet.user_id == UUID(user_id))
    )
    wallets = result.scalars().all()

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
    }


@router.get("/web-app/nfts")
async def web_app_get_user_nfts(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get user's NFTs for web app."""
    from uuid import UUID

    result = await db.execute(
        select(NFT).where(NFT.user_id == UUID(user_id))
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
                "status": nft.status,
                "image_url": nft.image_url,
                "minted_at": nft.minted_at.isoformat() if nft.minted_at else None,
                "created_at": nft.created_at.isoformat(),
            }
            for nft in nfts
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
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get active marketplace listings."""
    from app.models.marketplace import ListingStatus

    result = await db.execute(
        select(Listing, NFT)
        .where(Listing.status == ListingStatus.ACTIVE)
        .join(NFT, Listing.nft_id == NFT.id)
        .limit(limit)
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
