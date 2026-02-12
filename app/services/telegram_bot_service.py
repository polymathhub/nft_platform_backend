"""Telegram bot service for NFT operations."""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from app.models import User, Wallet, NFT, Collection
from app.models.marketplace import Listing, Offer, ListingStatus, OfferStatus
from app.config import get_settings
from app.services.nft_service import NFTService
from app.services.marketplace_service import MarketplaceService
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramBotService:
    """Telegram bot service."""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self):
        self.token = settings.telegram_bot_token
        self.api_url = f"{self.BASE_URL}{self.token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        logger.warning(f"[TELEGRAM] send_message called: chat_id={chat_id}, text_length={len(text)}")
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup

                logger.warning(f"[TELEGRAM] Posting to {self.api_url}/sendMessage")
                async with session.post(
                    f"{self.api_url}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    logger.warning(f"[TELEGRAM] Response status: {response.status}")
                    if response.status == 200:
                        logger.warning(f"[TELEGRAM] Message sent successfully to {chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to send message to {chat_id}: {response.status} - {error_text}"
                        )
                        return False
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}", exc_info=True)
            return False

    async def send_notification(
        self,
        user: User,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not user.telegram_id:
            logger.warning(f"User {user.id} has no Telegram ID")
            return False

        formatted_message = f"<b>{title}</b>\n\n{message}"
        if data:
            formatted_message += "\n\n"
            for key, value in data.items():
                formatted_message += f"<b>{key}:</b> <code>{value}</code>\n"

        return await self.send_message(
            chat_id=int(user.telegram_id),
            text=formatted_message,
        )

    async def handle_mint_command(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        wallet_id: str,
        nft_name: str,
        nft_description: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> tuple[Optional[NFT], str]:
        """
        Handle minting request from Telegram.
        Returns (NFT object or None, status message)
        """
        try:
            # Validate wallet ownership
            wallet_result = await db.execute(
                select(Wallet).where(
                    (Wallet.id == UUID(wallet_id)) & (Wallet.user_id == user.id)
                )
            )
            wallet = wallet_result.scalar_one_or_none()
            if not wallet:
                message = "❌ Wallet not found or not owned by you."
                await self.send_message(int(chat_id), message)
                return None, message

            # Mint NFT
            nft, error = await NFTService.mint_nft_with_blockchain_confirmation(
                db=db,
                user_id=user.id,
                wallet_id=UUID(wallet_id),
                name=nft_name,
                description=nft_description,
                image_url=image_url,
                royalty_percentage=0,
                metadata={"minted_via": "telegram"},
            )

            if error:
                message = f"❌ Minting failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            # Success notification
            success_message = (
                f"✅ <b>NFT Minted Successfully!</b>\n\n"
                f"<b>Name:</b> {nft.name}\n"
                f"<b>ID:</b> <code>{nft.global_nft_id}</code>\n"
                f"<b>Blockchain:</b> {nft.blockchain}\n"
                f"<b>Status:</b> {nft.status}"
            )
            await self.send_message(int(chat_id), success_message)
            return nft, "Minting successful"

        except ValueError as e:
            message = f"❌ Invalid wallet ID: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_mint_command: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    async def get_user_wallets(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[list[Wallet]]:
        """Get all wallets for a user."""
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalars().all()

    async def send_wallet_list(
        self, db: AsyncSession, chat_id: int, user_id: UUID
    ) -> bool:
        """Send user's available wallets as a formatted message with selection keyboard."""
        wallets = await self.get_user_wallets(db, user_id)

        if not wallets:
            return await self.send_message(
                chat_id,
                "❌ You don't have any wallets yet. Create one using /wallet-create &lt;blockchain&gt;.",
            )

        message = "<b>👛 Your Wallets:</b>\n\n"
        from app.ui.designer import build_wallet_selector
        
        wallet_data = []
        for i, wallet in enumerate(wallets, 1):
            primary_badge = "⭐" if wallet.is_primary else "  "
            message += (
                f"{primary_badge} {i}. <b>{wallet.name or f'Wallet {i}'}</b>\n"
                f"   Blockchain: <code>{wallet.blockchain.value.upper()}</code>\n"
                f"   Address: <code>{wallet.address[:10]}...{wallet.address[-10:]}</code>\n\n"
            )
            wallet_data.append({
                'id': str(wallet.id),
                'name': f"{wallet.blockchain.value.upper()}",
                'blockchain': wallet.blockchain.value
            })
        
        keyboard = build_wallet_selector(wallet_data)
        return await self.send_message(chat_id, message, reply_markup=keyboard)

    async def send_start_message(self, chat_id: int, username: str) -> bool:
        """Send welcome message with available commands."""
        message = (
            f"<b>Welcome to NFT Minting Bot, {username}! 🚀</b>\n\n"
            f"Available commands:\n"
            f"<code>/start</code> - Show this message\n"
            f"<code>/wallet</code> - List your wallets\n"
            f"<code>/mint &lt;wallet_id&gt; &lt;name&gt;</code> - Mint an NFT\n"
            f"<code>/status &lt;nft_id&gt;</code> - Check NFT status\n"
            f"<code>/help</code> - Show help\n\n"
            f"<b>Quick Start:</b>\n"
            f"1️⃣ View your wallets with /wallet\n"
            f"2️⃣ Use a wallet ID to mint NFTs\n"
            f"3️⃣ Track minting status with /status\n"
        )
        return await self.send_message(chat_id, message)

    async def send_nft_status(
        self, db: AsyncSession, chat_id: int, nft_id: str
    ) -> bool:
        """Send NFT minting status."""
        try:
            nft = await NFTService.get_nft_by_id(db, UUID(nft_id))
            if not nft:
                return await self.send_message(chat_id, "❌ NFT not found")

            status_emoji = {
                "pending": "⏳",
                "minted": "✅",
                "transferred": "↔️",
                "locked": "🔒",
                "burned": "🔥",
            }

            emoji = status_emoji.get(nft.status, "❓")

            message = (
                f"{emoji} <b>NFT Status</b>\n\n"
                f"<b>Name:</b> {nft.name}\n"
                f"<b>ID:</b> <code>{nft.global_nft_id}</code>\n"
                f"<b>Status:</b> <code>{nft.status}</code>\n"
                f"<b>Blockchain:</b> {nft.blockchain}\n"
            )

            if nft.minted_at:
                message += f"<b>Minted At:</b> {nft.minted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            if nft.token_id:
                message += f"<b>Token ID:</b> <code>{nft.token_id}</code>\n"
            if nft.transaction_hash:
                message += f"<b>Tx Hash:</b> <code>{nft.transaction_hash[:20]}...</code>\n"

            return await self.send_message(chat_id, message)
        except ValueError:
            return await self.send_message(chat_id, "❌ Invalid NFT ID format")
        except Exception as e:
            logger.error(f"Error sending NFT status: {e}")
            return await self.send_message(
                chat_id, f"❌ Error retrieving status: {str(e)}"
            )

    async def set_webhook(self, webhook_url: str) -> bool:
        """Set Telegram webhook for receiving updates."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"url": webhook_url}
                async with session.post(
                    f"{self.api_url}/setWebhook",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Webhook set successfully: {data}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to set webhook: {response.status} - {error_text}"
                        )
                        return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def delete_webhook(self) -> bool:
        """Delete Telegram webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/deleteWebhook",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        logger.info("Webhook deleted successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to delete webhook: {response.status} - {error_text}"
                        )
                        return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    # ==================== Marketplace Commands ====================

    async def send_user_nfts(
        self, db: AsyncSession, chat_id: int, user_id: UUID
    ) -> bool:
        """Send list of user's NFTs available for marketplace."""
        query = select(NFT).where(
            and_(NFT.user_id == user_id, NFT.status == "minted", NFT.is_locked == False)
        )
        result = await db.execute(query)
        nfts = result.scalars().all()

        if not nfts:
            return await self.send_message(
                chat_id,
                "❌ You don't have any unminted NFTs available for selling.\n\nMint an NFT first with /mint command.",
            )

        message = "<b>Your Available NFTs:</b>\n\n"
        for i, nft in enumerate(nfts[:10], 1):
            message += (
                f"{i}. <b>{nft.name}</b>\n"
                f"   ID: <code>{nft.id}</code>\n"
                f"   Status: {nft.status}\n"
                f"   Blockchain: {nft.blockchain}\n\n"
            )

        if len(nfts) > 10:
            message += f"... and {len(nfts) - 10} more\n"

        message += "\nUse <code>/list &lt;nft_id&gt; &lt;price&gt; [currency]</code> to list an NFT"
        return await self.send_message(chat_id, message)

    async def send_marketplace_listings(
        self, db: AsyncSession, chat_id: int, limit: int = 10
    ) -> bool:
        """Send active marketplace listings."""
        query = (
            select(Listing, NFT).where(
                and_(Listing.status == ListingStatus.ACTIVE, Listing.nft_id == NFT.id)
            )
            .limit(limit)
        )
        result = await db.execute(query)
        listings = result.all()

        if not listings:
            return await self.send_message(
                chat_id,
                "❌ No active listings in marketplace.",
            )

        message = "<b>Active Marketplace Listings:</b>\n\n"
        for i, (listing, nft) in enumerate(listings, 1):
            message += (
                f"{i}. <b>{nft.name}</b>\n"
                f"   Price: <code>{listing.price} {listing.currency}</code>\n"
                f"   NFT ID: <code>{listing.nft_id}</code>\n"
                f"   Listing ID: <code>{listing.id}</code>\n\n"
            )

        if await db.execute(select(Listing).where(Listing.status == ListingStatus.ACTIVE)) and len(listings) >= limit:
            message += f"Use /browse to see more listings\n"

        message += "\nUse <code>/offer &lt;listing_id&gt; &lt;price&gt;</code> to make an offer"
        return await self.send_message(chat_id, message)

    async def send_user_listings(
        self, db: AsyncSession, chat_id: int, user_id: UUID
    ) -> bool:
        """Send user's own listings."""
        query = select(Listing, NFT).where(
            and_(Listing.seller_id == user_id, Listing.nft_id == NFT.id)
        )
        result = await db.execute(query)
        listings = result.all()

        if not listings:
            return await self.send_message(
                chat_id,
                "❌ You have no active listings.",
            )

        message = "<b>Your Listings:</b>\n\n"
        for i, (listing, nft) in enumerate(listings, 1):
            status_emoji = "🟢" if listing.status == ListingStatus.ACTIVE else "🔴"
            message += (
                f"{status_emoji} {i}. <b>{nft.name}</b>\n"
                f"   Price: <code>{listing.price} {listing.currency}</code>\n"
                f"   Status: {listing.status}\n"
                f"   Listing ID: <code>{listing.id}</code>\n\n"
            )

        message += "\nUse <code>/cancel-listing &lt;listing_id&gt;</code> to cancel a listing"
        return await self.send_message(chat_id, message)

    async def handle_list_nft(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        nft_id: str,
        price: str,
        currency: str = "USDT",
    ) -> tuple[Optional[Listing], Optional[str]]:
        """Handle NFT listing on marketplace."""
        try:
            nft_uuid = UUID(nft_id)
            price_float = float(price)

            # Validate NFT ownership and status
            result = await db.execute(
                select(NFT).where(
                    and_(NFT.id == nft_uuid, NFT.user_id == user.id, NFT.is_locked == False)
                )
            )
            nft = result.scalar_one_or_none()
            
            if not nft:
                message = "❌ NFT not found, not owned by you, or already locked."
                await self.send_message(int(chat_id), message)
                return None, message

            # Get primary wallet
            wallet = await WalletService.get_primary_wallet(db, user.id, nft.blockchain)
            if not wallet:
                message = f"❌ No primary wallet for {nft.blockchain}."
                await self.send_message(int(chat_id), message)
                return None, message

            # Create listing
            listing, error = await MarketplaceService.create_listing(
                db=db,
                nft_id=nft_uuid,
                seller_id=user.id,
                seller_address=wallet.address,
                price=price_float,
                currency=currency.upper(),
                blockchain=nft.blockchain,
            )

            if error:
                message = f"❌ Listing failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            # Success notification
            success_message = (
                f"✅ <b>NFT Listed Successfully!</b>\n\n"
                f"<b>NFT:</b> {nft.name}\n"
                f"<b>Price:</b> <code>{listing.price} {listing.currency}</code>\n"
                f"<b>Listing ID:</b> <code>{listing.id}</code>\n"
                f"<b>Status:</b> {listing.status}"
            )
            await self.send_message(int(chat_id), success_message)
            return listing, "Listing successful"

        except ValueError as e:
            message = f"❌ Invalid input: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_list_nft: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    async def handle_make_offer(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        listing_id: str,
        offer_price: str,
    ) -> tuple[Optional[Offer], Optional[str]]:
        """Handle making an offer on a listing."""
        try:
            listing_uuid = UUID(listing_id)
            price_float = float(offer_price)

            # Get listing
            result = await db.execute(select(Listing).where(Listing.id == listing_uuid))
            listing = result.scalar_one_or_none()

            if not listing:
                message = "❌ Listing not found."
                await self.send_message(int(chat_id), message)
                return None, message

            if listing.seller_id == user.id:
                message = "❌ You cannot make offer on your own listing."
                await self.send_message(int(chat_id), message)
                return None, message

            # Get user wallet
            wallet = await WalletService.get_primary_wallet(db, user.id, listing.blockchain)
            if not wallet:
                message = f"❌ No primary wallet for {listing.blockchain}."
                await self.send_message(int(chat_id), message)
                return None, message

            # Make offer
            offer, error = await MarketplaceService.make_offer(
                db=db,
                listing_id=listing_uuid,
                buyer_id=user.id,
                buyer_address=wallet.address,
                offer_price=price_float,
                currency=listing.currency,
            )

            if error:
                message = f"❌ Offer failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            # Success notification
            success_message = (
                f"✅ <b>Offer Made Successfully!</b>\n\n"
                f"<b>Offer Price:</b> <code>{offer.offer_price} {offer.currency}</code>\n"
                f"<b>Listing Price:</b> <code>{listing.price} {listing.currency}</code>\n"
                f"<b>Offer ID:</b> <code>{offer.id}</code>\n"
                f"<b>Status:</b> {offer.status}"
            )
            await self.send_message(int(chat_id), success_message)
            return offer, "Offer successful"

        except ValueError as e:
            message = f"❌ Invalid input: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_make_offer: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    async def handle_cancel_listing(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        listing_id: str,
    ) -> tuple[Optional[Listing], Optional[str]]:
        """Handle cancelling a listing."""
        try:
            listing_uuid = UUID(listing_id)

            # Cancel listing
            listing, error = await MarketplaceService.cancel_listing(
                db=db,
                listing_id=listing_uuid,
                user_id=user.id,
            )

            if error:
                message = f"❌ Cancel failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            # Success notification
            success_message = (
                f"✅ <b>Listing Cancelled!</b>\n\n"
                f"<b>NFT:</b> Unlocked for other operations\n"
                f"<b>Listing ID:</b> <code>{listing.id}</code>"
            )
            await self.send_message(int(chat_id), success_message)
            return listing, "Cancellation successful"

        except ValueError as e:
            message = f"❌ Invalid listing ID: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_cancel_listing: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    # ==================== Wallet Commands ====================

    async def send_wallet_creation_guide(self, chat_id: int) -> bool:
        """Send wallet creation guide."""
        message = (
            "<b>📱 Wallet Management</b>\n\n"
            "Commands:\n"
            "<code>/wallets</code> - List your wallets\n"
            "<code>/wallet-create &lt;blockchain&gt;</code> - Create new wallet\n"
            "<code>/wallet-import &lt;blockchain&gt; &lt;address&gt;</code> - Import wallet\n"
            "<code>/set-primary &lt;wallet_id&gt;</code> - Set primary wallet\n\n"
            "<b>Supported Blockchains:</b>\n"
            "• ethereum\n"
            "• solana\n"
            "• polygon\n"
            "• ton\n"
            "• bitcoin\n\n"
            "Example:\n"
            "<code>/wallet-create ethereum</code>"
        )
        return await self.send_message(chat_id, message)

    async def handle_wallet_create(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        blockchain: str,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Handle wallet creation for a blockchain."""
        try:
            from app.models.wallet import BlockchainType, WalletType
            import hashlib
            
            blockchain_lower = blockchain.lower()
            try:
                blockchain_type = BlockchainType(blockchain_lower)
            except ValueError:
                message = f"❌ Unsupported blockchain: {blockchain}\n\nSupported: ethereum, solana, polygon, ton, bitcoin, arbitrum, optimism, base, avalanche"
                await self.send_message(chat_id, message)
                return None, message
            
            user_hash = hashlib.sha256(f"{user.id}{blockchain_lower}".encode()).hexdigest()[:16]
            blockchain_address = f"0x{user_hash}"
            
            wallet_metadata = {
                "name": f"{blockchain.capitalize()} Wallet",
                "created_via": "telegram",
                "wallet_index": 1
            }
            
            wallet, error = await WalletService.create_wallet(
                db=db,
                user_id=user.id,
                blockchain=blockchain_type,
                wallet_type=WalletType.SELF_CUSTODY,
                address=blockchain_address,
                is_primary=True,
                public_key=None,
                mnemonic=None,
            )
            
            if error:
                message = f"❌ Wallet creation failed: {error}"
                await self.send_message(chat_id, message)
                return None, message
            
            wallet.wallet_metadata = wallet_metadata
            await db.commit()
            await db.refresh(wallet)
            
            success_message = (
                f"✅ <b>Wallet Created Successfully!</b>\n\n"
                f"<b>🔗 Blockchain:</b> <code>{blockchain.upper()}</code>\n"
                f"<b>📍 Address:</b> <code>{wallet.address}</code>\n"
                f"<b>📋 Type:</b> Self-Custody\n"
                f"<b>🆔 Wallet ID:</b> <code>{str(wallet.id)}</code>\n"
                f"<b>⭐ Primary:</b> Yes\n\n"
                f"<i>Keep your address safe. You can use this wallet for minting and trading.</i>"
            )
            await self.send_message(chat_id, success_message)
            return wallet, None
            
        except Exception as e:
            logger.error(f"Error in handle_wallet_create: {e}", exc_info=True)
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(chat_id, message)
            return None, str(e)
    
    async def handle_wallet_import(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        blockchain: str,
        address: str,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Handle wallet import for a blockchain."""
        try:
            from app.models.wallet import BlockchainType, WalletType
            
            blockchain_lower = blockchain.lower()
            try:
                blockchain_type = BlockchainType(blockchain_lower)
            except ValueError:
                message = f"❌ Unsupported blockchain: {blockchain}\n\nSupported: ethereum, solana, polygon, ton, bitcoin, arbitrum, optimism, base, avalanche"
                await self.send_message(chat_id, message)
                return None, message
            
            wallet_metadata = {
                "name": f"Imported {blockchain.capitalize()} Wallet",
                "created_via": "telegram_import",
                "import_date": datetime.utcnow().isoformat()
            }
            
            wallet, error = await WalletService.import_wallet(
                db=db,
                user_id=user.id,
                blockchain=blockchain_type,
                address=address,
                is_primary=True,
            )
            
            if error:
                message = f"❌ Wallet import failed: {error}"
                await self.send_message(chat_id, message)
                return None, message
            
            wallet.wallet_metadata = wallet_metadata
            await db.commit()
            await db.refresh(wallet)
            
            success_message = (
                f"✅ <b>Wallet Imported Successfully!</b>\n\n"
                f"<b>🔗 Blockchain:</b> <code>{blockchain.upper()}</code>\n"
                f"<b>📍 Address:</b> <code>{address}</code>\n"
                f"<b>📋 Type:</b> Self-Custody (Imported)\n"
                f"<b>🆔 Wallet ID:</b> <code>{str(wallet.id)}</code>\n"
                f"<b>⭐ Primary:</b> Yes\n\n"
                f"<i>Your wallet has been added to your account.</i>"
            )
            await self.send_message(chat_id, success_message)
            return wallet, None
            
        except Exception as e:
            logger.error(f"Error in handle_wallet_import: {e}", exc_info=True)
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(chat_id, message)
            return None, str(e)

    async def handle_set_primary_wallet(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        wallet_id: str,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Handle setting primary wallet."""
        try:
            wallet_uuid = UUID(wallet_id)

            wallet, error = await WalletService.set_primary_wallet(
                db=db,
                user_id=user.id,
                wallet_id=wallet_uuid,
            )

            if error:
                message = f"❌ Failed to set primary wallet: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            wallet_name = wallet.wallet_metadata.get('name', 'Wallet') if wallet.wallet_metadata else 'Wallet'
            wallet_type_label = wallet.wallet_type.value.replace('_', ' ').title()
            
            success_message = (
                f"✅ <b>Primary Wallet Updated!</b>\n\n"
                f"<b>💼 Wallet:</b> {wallet_name}\n"
                f"<b>🔗 Blockchain:</b> <code>{wallet.blockchain.value.upper()}</code>\n"
                f"<b>📍 Address:</b> <code>{wallet.address}</code>\n"
                f"<b>📋 Type:</b> {wallet_type_label}\n"
                f"<b>⭐ Status:</b> Now Primary\n"
                f"<b>🆔 ID:</b> <code>{str(wallet.id)}</code>"
            )
            await self.send_message(int(chat_id), success_message)
            return wallet, "Primary wallet set"

        except ValueError as e:
            message = f"❌ Invalid wallet ID: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_set_primary_wallet: {e}", exc_info=True)
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    # ==================== NFT Operations ====================

    async def handle_transfer_nft(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        nft_id: str,
        to_address: str,
    ) -> tuple[Optional[NFT], Optional[str]]:
        """Handle NFT transfer."""
        try:
            nft_uuid = UUID(nft_id)

            # Verify ownership
            result = await db.execute(
                select(NFT).where(and_(NFT.id == nft_uuid, NFT.user_id == user.id))
            )
            nft = result.scalar_one_or_none()

            if not nft:
                message = "❌ NFT not found or not owned by you."
                await self.send_message(int(chat_id), message)
                return None, message

            if nft.is_locked:
                message = "❌ NFT is locked and cannot be transferred."
                await self.send_message(int(chat_id), message)
                return None, message

            # Transfer NFT
            transferred_nft, error = await NFTService.transfer_nft(
                db=db,
                nft_id=nft_uuid,
                to_address=to_address,
                transaction_hash="",  # Will be updated with actual tx
            )

            if error:
                message = f"❌ Transfer failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            success_message = (
                f"✅ <b>Transfer Initiated!</b>\n\n"
                f"<b>NFT:</b> {nft.name}\n"
                f"<b>To Address:</b> <code>{to_address[:20]}...</code>\n"
                f"<b>Status:</b> {transferred_nft.status}"
            )
            await self.send_message(int(chat_id), success_message)
            return transferred_nft, "Transfer initiated"

        except ValueError as e:
            message = f"❌ Invalid input: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_transfer_nft: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    async def handle_burn_nft(
        self,
        db: AsyncSession,
        chat_id: int,
        user: User,
        nft_id: str,
    ) -> tuple[Optional[NFT], Optional[str]]:
        """Handle NFT burning."""
        try:
            nft_uuid = UUID(nft_id)

            # Verify ownership
            result = await db.execute(
                select(NFT).where(and_(NFT.id == nft_uuid, NFT.user_id == user.id))
            )
            nft = result.scalar_one_or_none()

            if not nft:
                message = "❌ NFT not found or not owned by you."
                await self.send_message(int(chat_id), message)
                return None, message

            if nft.is_locked:
                message = "❌ NFT is locked and cannot be burned."
                await self.send_message(int(chat_id), message)
                return None, message

            # Burn NFT
            burned_nft, error = await NFTService.burn_nft(
                db=db,
                nft_id=nft_uuid,
                transaction_hash="",  # Will be updated with actual tx
            )

            if error:
                message = f"❌ Burn failed: {error}"
                await self.send_message(int(chat_id), message)
                return None, message

            success_message = (
                f"✅ <b>NFT Burn Initiated!</b>\n\n"
                f"<b>NFT:</b> {nft.name}\n"
                f"<b>Status:</b> {burned_nft.status}"
            )
            await self.send_message(int(chat_id), success_message)
            return burned_nft, "Burn initiated"

        except ValueError as e:
            message = f"❌ Invalid NFT ID: {e}"
            await self.send_message(int(chat_id), message)
            return None, message
        except Exception as e:
            logger.error(f"Error in handle_burn_nft: {e}")
            message = f"❌ An error occurred: {str(e)}"
            await self.send_message(int(chat_id), message)
            return None, message

    # ==================== Notification Send ====================

    async def send_nft_minted_notification(
        self,
        user: User,
        nft: NFT,
    ) -> bool:
        """Send NFT minted notification."""
        return await self.send_notification(
            user=user,
            title="🎉 NFT Minted!",
            message=f"Your NFT '{nft.name}' has been successfully minted.",
            data={
                "nft_id": str(nft.id),
                "nft_name": nft.name,
                "blockchain": nft.blockchain,
                "status": nft.status,
            },
        )

    async def send_listing_created_notification(
        self,
        user: User,
        listing: Listing,
        nft_name: str,
    ) -> bool:
        """Send listing created notification."""
        return await self.send_notification(
            user=user,
            title="📢 Listing Created!",
            message=f"Your NFT '{nft_name}' is now listed on marketplace.",
            data={
                "listing_id": str(listing.id),
                "price": str(listing.price),
                "currency": listing.currency,
            },
        )

    async def send_offer_received_notification(
        self,
        user: User,
        offer: Offer,
        nft_name: str,
    ) -> bool:
        """Send offer received notification."""
        return await self.send_notification(
            user=user,
            title="💰 New Offer!",
            message=f"You received an offer for '{nft_name}'.",
            data={
                "offer_id": str(offer.id),
                "offer_price": str(offer.offer_price),
                "currency": offer.currency,
            },
        )

    async def send_transaction_confirmation_notification(
        self,
        user: User,
        tx_hash: str,
        tx_type: str,
        status: str,
    ) -> bool:
        """Send transaction confirmation notification."""
        return await self.send_notification(
            user=user,
            title="✅ Transaction Confirmed!",
            message=f"Your {tx_type} transaction has been confirmed on blockchain.",
            data={
                "transaction_hash": tx_hash,
                "type": tx_type,
                "status": status,
            },
        )