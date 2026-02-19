import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import User, Wallet, NFT, Collection
from app.models import Escrow
from app.models.wallet import BlockchainType, WalletType
from app.utils.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.config import get_settings
from app.utils.blockchain_utils import USDTHelper
from app.blockchain.ethereum_client import EthereumClient
from app.models.marketplace import Offer, Listing
from app.models import EscrowStatus
import os
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import serialization
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()


class WalletService:
    """Service for wallet operations."""

    @staticmethod
    async def create_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: BlockchainType,
        wallet_type: WalletType,
        address: str,
        is_primary: bool = False,
        public_key: Optional[str] = None,
        mnemonic: Optional[str] = None,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        existing = await db.execute(
            select(Wallet).where(Wallet.address == address)
        )
        if existing.scalar_one_or_none():
            return None, "Wallet address already registered"

        if is_primary:
            result = await db.execute(
                select(Wallet).where(
                    and_(
                        Wallet.user_id == user_id,
                        Wallet.blockchain == blockchain,
                        Wallet.is_primary == True,
                    )
                )
            )
            for wallet in result.scalars().all():
                wallet.is_primary = False

        encrypted_mnemonic = None
        if mnemonic:
            encrypted_mnemonic = encrypt_sensitive_data(mnemonic, settings.mnemonic_encryption_key)

        new_wallet = Wallet(
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=wallet_type,
            address=address,
            public_key=public_key,
            encrypted_private_key=None,
            encrypted_mnemonic=encrypted_mnemonic,
            is_primary=is_primary,
            wallet_metadata={
                "created_by": "api",
                "wallet_type": wallet_type.value,
            },
        )
        db.add(new_wallet)
        await db.commit()
        await db.refresh(new_wallet)
        return new_wallet, None

    @staticmethod
    async def import_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: BlockchainType,
        address: str,
        is_primary: bool = False,
        public_key: Optional[str] = None,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        return await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=WalletType.SELF_CUSTODY,
            address=address,
            is_primary=is_primary,
            public_key=public_key,
        )

    @staticmethod
    async def get_user_wallets(
        db: AsyncSession,
        user_id: UUID,
        blockchain: Optional[BlockchainType] = None,
    ) -> list[Wallet]:
        query = select(Wallet).where(Wallet.user_id == user_id)
        if blockchain:
            query = query.where(Wallet.blockchain == blockchain)
        result = await db.execute(query.order_by(Wallet.is_primary.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_primary_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: BlockchainType,
    ) -> Optional[Wallet]:
        result = await db.execute(
            select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.blockchain == blockchain,
                    Wallet.is_primary == True,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set_primary_wallet(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        result = await db.execute(
            select(Wallet).where(and_(Wallet.id == wallet_id, Wallet.user_id == user_id))
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            return None, "Wallet not found"

        result_wallets = await db.execute(
            select(Wallet).where(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.blockchain == wallet.blockchain,
                    Wallet.is_primary == True,
                )
            )
        )
        for w in result_wallets.scalars().all():
            w.is_primary = False

        wallet.is_primary = True
        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def deactivate_wallet(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        result = await db.execute(
            select(Wallet).where(and_(Wallet.id == wallet_id, Wallet.user_id == user_id))
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            return None, "Wallet not found"

        if wallet.is_primary:
            return None, "Cannot deactivate primary wallet"

        wallet.is_active = False
        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def get_wallet_by_address(
        db: AsyncSession,
        address: str,
    ) -> Optional[Wallet]:
        result = await db.execute(select(Wallet).where(Wallet.address == address))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_wallet_by_id(
        db: AsyncSession,
        wallet_id: UUID,
    ) -> Optional[Wallet]:
        result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
        return result.scalar_one_or_none()

    # ------------------ Escrow / Hold helpers ------------------
    @staticmethod
    async def create_escrow_hold(
        db: AsyncSession,
        listing_id: UUID,
        offer_id: UUID,
        buyer_id: UUID,
        seller_id: UUID,
        amount: float,
        currency: str,
        commission_pct: float = 0.02,
    ) -> tuple[Optional[Escrow], Optional[str]]:
        """Create an escrow record representing funds held by platform custody.

        Note: Actual on-chain custody operations are out of scope for this helper;
        this records the intent and marks funds as HELD so business logic can proceed.
        """
        try:
            commission = round(amount * commission_pct, 8)
            escrow = Escrow(
                listing_id=listing_id,
                offer_id=offer_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                amount=amount,
                currency=currency,
                commission_amount=commission,
                status=EscrowStatus.HELD,
            )
            db.add(escrow)
            await db.commit()
            await db.refresh(escrow)
            return escrow, None
        except Exception as e:
            logger.error(f"Failed to create escrow hold: {e}")
            return None, str(e)

    @staticmethod
    async def release_escrow(
        db: AsyncSession,
        escrow_id: UUID,
        tx_hash: Optional[str] = None,
    ) -> tuple[Optional[Escrow], Optional[str]]:
        # Load escrow and related records
        try:
            res = await db.execute(select(Escrow).where(Escrow.id == escrow_id))
            escrow = res.scalar_one_or_none()
            if not escrow:
                return None, "Escrow not found"

            # Default: mark released and return if no on-chain payout possible
            listing_res = await db.execute(select(Listing).where(Listing.id == escrow.listing_id))
            listing = listing_res.scalar_one_or_none()

            offer_res = await db.execute(select(Offer).where(Offer.id == escrow.offer_id))
            offer = offer_res.scalar_one_or_none()

            nft = None
            royalty_amount = 0
            if listing:
                nft_res = await db.execute(select(NFT).where(NFT.id == listing.nft_id))
                nft = nft_res.scalar_one_or_none()
                if nft and offer:
                    royalty_amount = float(offer.offer_price) * (nft.royalty_percentage / 100)

            # If this is a USDT escrow on an EVM chain and platform has keys configured, attempt on-chain payouts
            if escrow.currency and escrow.currency.upper() == "USDT" and listing and listing.blockchain.lower() in ("ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"):
                chain_key = listing.blockchain.lower()
                platform_key = getattr(settings, "platform_private_keys", {}).get(chain_key)
                platform_addr = getattr(settings, "platform_wallets", {}).get(chain_key)
                contract = USDTHelper.get_usdt_contract(listing.blockchain, settings)

                if platform_key and platform_addr and contract and offer:
                    client = EthereumClient()
                    # compute amounts
                    commission = float(escrow.commission_amount or 0)
                    total_amount = float(escrow.amount)
                    royalty = float(royalty_amount or 0)
                    seller_amount = total_amount - commission - royalty

                    if seller_amount < 0:
                        return None, "Computed seller payout is negative"

                    seller_addr = listing.seller_address

                    # convert to raw token units
                    seller_raw = USDTHelper.parse_usdt(seller_amount)
                    royalty_raw = USDTHelper.parse_usdt(royalty)

                    payout_tx = None
                    royalty_tx = None

                    # Send seller payout from platform custody
                    try:
                        payout_tx, payout_err = await client.send_erc20_transfer(platform_key, contract, seller_addr, seller_raw)
                        if payout_err:
                            logger.error(f"Seller payout failed for escrow {escrow.id}: {payout_err}")
                    except Exception as e:
                        payout_tx = None
                        payout_err = str(e)
                        logger.error(f"Seller payout exception for escrow {escrow.id}: {e}")

                    # Send royalty if applicable to collection creator
                    if royalty > 0 and nft and nft.collection_id:
                        # find collection creator primary wallet
                        from app.models import Collection, User as UserModel

                        coll_res = await db.execute(select(Collection).where(Collection.id == nft.collection_id))
                        collection = coll_res.scalar_one_or_none()
                        if collection:
                            creator_res = await db.execute(select(UserModel).where(UserModel.id == collection.creator_id))
                            creator = creator_res.scalar_one_or_none()
                            if creator:
                                # get creator primary wallet for chain
                                creator_wallet_res = await db.execute(select(Wallet).where(and_(Wallet.user_id == creator.id, Wallet.blockchain == listing.blockchain)))
                                creator_wallet = creator_wallet_res.scalar_one_or_none()
                                if creator_wallet and creator_wallet.address:
                                    try:
                                        royalty_tx, royalty_err = await client.send_erc20_transfer(platform_key, contract, creator_wallet.address, royalty_raw)
                                        if royalty_err:
                                            logger.error(f"Royalty payout failed for escrow {escrow.id}: {royalty_err}")
                                    except Exception as e:
                                        royalty_tx = None
                                        royalty_err = str(e)
                                        logger.error(f"Royalty payout exception for escrow {escrow.id}: {e}")

                    # Update escrow metadata with payout txs
                    meta = escrow.escrow_metadata or {}
                    if payout_tx:
                        meta["payout_tx"] = payout_tx
                    else:
                        meta["payout_error"] = payout_err if 'payout_err' in locals() else "unknown"
                    if royalty_tx:
                        meta["royalty_tx"] = royalty_tx
                    elif 'royalty_err' in locals() and royalty_err:
                        meta["royalty_error"] = royalty_err
                    escrow.escrow_metadata = meta
                    escrow.tx_hash = tx_hash or escrow.tx_hash
                    escrow.status = EscrowStatus.RELEASED
                    escrow.updated_at = datetime.utcnow()
                    await db.commit()
                    await db.refresh(escrow)
                    return escrow, None

            # Fallback: just mark released without on-chain payout
            escrow.status = EscrowStatus.RELEASED
            if tx_hash:
                escrow.tx_hash = tx_hash
            escrow.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(escrow)
            return escrow, None
        except Exception as e:
            logger.error(f"Failed to release escrow: {e}", exc_info=True)
            return None, str(e)


    @staticmethod
    async def refund_escrow(db: AsyncSession, escrow_id: UUID, reason: Optional[str] = None):
        result = await db.execute(select(Escrow).where(Escrow.id == escrow_id))
        escrow = result.scalar_one_or_none()
        if not escrow:
            return False, "Escrow not found"

        if escrow.status not in (EscrowStatus.HELD, EscrowStatus.PENDING, EscrowStatus.DISPUTED):
            return False, f"Cannot refund escrow with status {escrow.status}"

        escrow.status = EscrowStatus.REFUNDED
        meta = escrow.escrow_metadata or {}
        meta["refund_reason"] = reason
        escrow.escrow_metadata = meta
        escrow.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(escrow)
        return True, None

    @staticmethod
    async def create_escrow_pending(
        db: AsyncSession,
        listing_id: UUID,
        offer_id: UUID,
        buyer_id: UUID,
        seller_id: UUID,
        amount: float,
        currency: str,
        commission_pct: float = 0.02,
    ) -> tuple[Optional[Escrow], Optional[str]]:
        """Create an escrow record with status PENDING while awaiting external deposit."""
        try:
            commission = round(amount * commission_pct, 8)
            escrow = Escrow(
                listing_id=listing_id,
                offer_id=offer_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                amount=amount,
                currency=currency,
                commission_amount=commission,
                status=EscrowStatus.PENDING,
            )
            db.add(escrow)
            await db.commit()
            await db.refresh(escrow)
            return escrow, None
        except Exception as e:
            logger.error(f"Failed to create pending escrow: {e}")
            return None, str(e)

    @staticmethod
    async def verify_deposit_for_offer(db: AsyncSession, offer_id: UUID, tx_hash: str) -> tuple[Optional[Escrow], Optional[str]]:
        """Verify external deposit (tx_hash) and mark escrow HELD if valid.

        Currently supports EVM USDT verification by checking Transfer logs against platform address.
        """
        # Find escrow
        res = await db.execute(select(Escrow).where(Escrow.offer_id == offer_id))
        escrow = res.scalar_one_or_none()
        if not escrow:
            return None, "Escrow not found for offer"

        if escrow.status not in (EscrowStatus.PENDING, EscrowStatus.DISPUTED):
            return None, f"Escrow not in pending state: {escrow.status}"

        # Load offer/listing to determine blockchain
        offer_res = await db.execute(select(Offer).where(Offer.id == offer_id))
        offer = offer_res.scalar_one_or_none()
        if not offer:
            return None, "Offer not found"

        listing_res = await db.execute(select(Listing).where(Listing.id == offer.listing_id))
        listing = listing_res.scalar_one_or_none()
        if not listing:
            return None, "Listing not found"

        # Only USDT supported for deposit verification for now
        if offer.currency.upper() != "USDT":
            return None, "Only USDT deposits are supported currently"

        # Only EVM chains supported in verification implementation
        if listing.blockchain.lower() not in ("ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"):
            return None, f"Deposit verification not implemented for {listing.blockchain}"

        # Determine USDT contract and platform address
        contract = USDTHelper.get_usdt_contract(listing.blockchain, settings)
        platform_addr = settings.platform_wallets.get(listing.blockchain.lower()) if hasattr(settings, 'platform_wallets') else None
        if not contract or not platform_addr:
            return None, "Platform configuration missing for deposit verification"

        # Fetch tx receipt
        client = EthereumClient()
        receipt = await client.get_transaction_receipt(tx_hash)
        if not receipt:
            return None, "Transaction not found"

        # Transfer event signature
        transfer_sig = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

        logs = receipt.get("logs", [])
        expected_amount_raw = USDTHelper.parse_usdt(float(escrow.amount))

        found = False
        for log in logs:
            # Match token contract
            log_addr = log.get("address", "").lower()
            if log_addr != contract.lower():
                continue
            topics = log.get("topics", [])
            if not topics or topics[0].lower() != transfer_sig:
                continue
            # topics[2] is to address (padded). Compare last 40 hex chars
            if len(topics) < 3:
                continue
            to_topic = topics[2]
            # remove 0x
            to_hex = to_topic[2:] if to_topic.startswith("0x") else to_topic
            to_addr = "0x" + to_hex[-40:]
            if to_addr.lower() != platform_addr.lower():
                continue
            # parse data value
            data = log.get("data", "0x0")
            value = int(data, 16) if isinstance(data, str) and data.startswith("0x") else int(data)
            if value >= expected_amount_raw:
                found = True
                break

        if not found:
            return None, "No matching USDT transfer to platform address found in transaction"

        # Mark escrow held
        escrow.status = EscrowStatus.HELD
        escrow.tx_hash = tx_hash
        escrow.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(escrow)
        return escrow, None
    # ------------------ Wallet generation helpers ------------------
    @staticmethod
    async def generate_evm_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: Optional[BlockchainType] = None,
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a single EVM wallet (shared across EVM-compatible chains).

        Uses SECP256K1 private key and Keccak-256 for address derivation.
        Requires a keccak implementation (pysha3) available as `sha3` or
        Crypto.Hash.keccak. Encrypted private key is stored using existing
        `encrypt_sensitive_data` and `mnemonic_encryption_key`.
        """
        # Default to Ethereum if no blockchain specified
        blockchain = blockchain or BlockchainType.ETHEREUM
        
        # Idempotent: if user already has an EVM wallet for this blockchain, check if it exists
        existing = await WalletService.get_user_wallets(db, user_id, BlockchainType.ETHEREUM)
        if existing and blockchain == BlockchainType.ETHEREUM:
            return existing[0], None

        # Generate secp256k1 private key
        try:
            priv_key_obj = ec.generate_private_key(ec.SECP256K1())
            priv_bytes = priv_key_obj.private_numbers().private_value.to_bytes(32, "big")
            # public key uncompressed
            pub_bytes = priv_key_obj.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint,
            )
        except Exception as e:
            logger.error(f"Failed to generate EVM keypair: {e}")
            return None, "Key generation failed"

        # Keccak-256 over public key (skip 0x04 prefix)
        keccak_digest = None
        try:
            import sha3 as _sha3

            k = _sha3.keccak_256()
            k.update(pub_bytes[1:])
            keccak_digest = k.digest()
        except Exception:
            try:
                from Crypto.Hash import keccak as _keccak

                k = _keccak.new(digest_bits=256)
                k.update(pub_bytes[1:])
                keccak_digest = k.digest()
            except Exception:
                return None, (
                    "Keccak implementation not available. Install 'pysha3' or 'pycryptodome'"
                )

        address = "0x" + keccak_digest[-20:].hex()

        # Encrypt private key
        encrypted = encrypt_sensitive_data(priv_bytes.hex(), settings.mnemonic_encryption_key)

        # Create wallet record for the specific blockchain (or ETHEREUM as default)
        wallet, err = await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=WalletType.CUSTODIAL,
            address=address,
            is_primary=make_primary,
            public_key=pub_bytes.hex(),
            mnemonic=None,
        )
        if err:
            return None, err

        # Persist encrypted private key and mark metadata with evm_chains
        wallet.encrypted_private_key = encrypted
        try:
            wallet.wallet_metadata = wallet.wallet_metadata or {}
            wallet.wallet_metadata["evm_chains"] = [
                BlockchainType.ETHEREUM.value,
                BlockchainType.POLYGON.value,
                BlockchainType.ARBITRUM.value,
                BlockchainType.OPTIMISM.value,
                BlockchainType.BASE.value,
                BlockchainType.AVALANCHE.value,
            ]
        except Exception:
            # ensure metadata is a dict
            wallet.wallet_metadata = {"evm_chains": [BlockchainType.ETHEREUM.value]}

        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def generate_solana_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: Optional[BlockchainType] = None,
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate an Ed25519 keypair for Solana and store encrypted private key.

        Uses base58 encoding for the public key/address. A small internal
        base58 encoder is included to avoid adding external deps.
        """
        # Default to Solana if no blockchain specified
        blockchain = blockchain or BlockchainType.SOLANA
        
        # Idempotent
        existing = await WalletService.get_user_wallets(db, user_id, BlockchainType.SOLANA)
        if existing:
            return existing[0], None

        # generate ed25519 keypair
        try:
            sk = ed25519.Ed25519PrivateKey.generate()
            sk_bytes = sk.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
            pk = sk.public_key()
            pk_bytes = pk.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except Exception as e:
            logger.error(f"Solana keygen failed: {e}")
            return None, "Solana key generation failed"

        # base58 encode function
        ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

        def b58encode(b: bytes) -> str:
            num = int.from_bytes(b, "big")
            enc = ""
            while num > 0:
                num, rem = divmod(num, 58)
                enc = ALPHABET[rem] + enc
            # leading zeros
            n_pad = 0
            for c in b:
                if c == 0:
                    n_pad += 1
                else:
                    break
            return ALPHABET[0] * n_pad + enc

        address = b58encode(pk_bytes)

        encrypted = encrypt_sensitive_data(sk_bytes.hex(), settings.mnemonic_encryption_key)

        wallet, err = await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=WalletType.CUSTODIAL,
            address=address,
            is_primary=make_primary,
            public_key=pk_bytes.hex(),
            mnemonic=None,
        )
        if err:
            return None, err

        wallet.encrypted_private_key = encrypted
        wallet.wallet_metadata = wallet.wallet_metadata or {}
        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def generate_bitcoin_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: Optional[BlockchainType] = None,
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a Bitcoin P2PKH address (base58check) using secp256k1.

        This implementation creates a compressed public key and P2PKH address.
        It relies on hashlib supporting RIPEMD160; if not available, it will
        raise an informative error.
        """
        # Default to Bitcoin if no blockchain specified
        blockchain = blockchain or BlockchainType.BITCOIN
        
        existing = await WalletService.get_user_wallets(db, user_id, BlockchainType.BITCOIN)
        if existing:
            return existing[0], None

        # generate secp256k1 key
        try:
            priv_key_obj = ec.generate_private_key(ec.SECP256K1())
            priv_bytes = priv_key_obj.private_numbers().private_value.to_bytes(32, "big")
            pub_point = priv_key_obj.public_key()
            # compressed pubkey format
            numbers = pub_point.public_numbers()
            x = numbers.x.to_bytes(32, "big")
            y = numbers.y
            prefix = b"\x02" if (y % 2 == 0) else b"\x03"
            compressed_pub = prefix + x
        except Exception as e:
            logger.error(f"Bitcoin keygen failed: {e}")
            return None, "Bitcoin key generation failed"

        # HASH160 = RIPEMD160(SHA256(pubkey))
        try:
            sha256 = hashlib.sha256(compressed_pub).digest()
            h = hashlib.new("ripemd160")
            h.update(sha256)
            pubkey_hash = h.digest()
        except Exception as e:
            logger.error(f"RIPEMD160 hashing not available: {e}")
            return None, "RIPEMD160 not available in hashlib"

        # version byte 0x00 for mainnet
        versioned = b"\x00" + pubkey_hash
        checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
        addr_bytes = versioned + checksum

        # base58 encode
        ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

        def b58encode(b: bytes) -> str:
            num = int.from_bytes(b, "big")
            enc = ""
            while num > 0:
                num, rem = divmod(num, 58)
                enc = ALPHABET[rem] + enc
            # leading zeros
            n_pad = 0
            for c in b:
                if c == 0:
                    n_pad += 1
                else:
                    break
            return ALPHABET[0] * n_pad + enc

        address = b58encode(addr_bytes)

        encrypted = encrypt_sensitive_data(priv_bytes.hex(), settings.mnemonic_encryption_key)

        wallet, err = await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=WalletType.CUSTODIAL,
            address=address,
            is_primary=make_primary,
            public_key=compressed_pub.hex(),
            mnemonic=None,
        )
        if err:
            return None, err

        wallet.encrypted_private_key = encrypted
        wallet.wallet_metadata = wallet.wallet_metadata or {}
        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def generate_ton_wallet(
        db: AsyncSession,
        user_id: UUID,
        blockchain: Optional[BlockchainType] = None,
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a TON wallet keypair (Ed25519) and store encrypted key.

        TON address encoding differs from Solana; for now store public key
        base64 as the address and set metadata.workchain when available.
        """
        # Default to TON if no blockchain specified
        blockchain = blockchain or BlockchainType.TON
        
        existing = await WalletService.get_user_wallets(db, user_id, BlockchainType.TON)
        if existing:
            return existing[0], None

        try:
            sk = ed25519.Ed25519PrivateKey.generate()
            sk_bytes = sk.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
            pk = sk.public_key()
            pk_bytes = pk.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except Exception as e:
            logger.error(f"TON keygen failed: {e}")
            return None, "TON key generation failed"

        address = base64.b64encode(pk_bytes).decode()
        encrypted = encrypt_sensitive_data(sk_bytes.hex(), settings.mnemonic_encryption_key)

        wallet, err = await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=blockchain,
            wallet_type=WalletType.CUSTODIAL,
            address=address,
            is_primary=make_primary,
            public_key=pk_bytes.hex(),
            mnemonic=None,
        )
        if err:
            return None, err

        wallet.encrypted_private_key = encrypted
        wallet.wallet_metadata = wallet.wallet_metadata or {}
        await db.commit()
        await db.refresh(wallet)
        return wallet, None

    @staticmethod
    async def generate_wallet_bundle(
        db: AsyncSession,
        user_id: UUID,
        make_primary: bool = True,
    ) -> dict:
        """Generate EVM (single record), Solana, Bitcoin, and TON wallets for user.

        Returns a mapping of blockchain -> address. Idempotent: existing wallets
        will not be regenerated.
        """
        result = {}

        evm_wallet, err = await WalletService.generate_evm_wallet(db, user_id, make_primary)
        if evm_wallet:
            result[BlockchainType.ETHEREUM.value] = evm_wallet.address

        sol_wallet, err = await WalletService.generate_solana_wallet(db, user_id, False)
        if sol_wallet:
            result[BlockchainType.SOLANA.value] = sol_wallet.address

        btc_wallet, err = await WalletService.generate_bitcoin_wallet(db, user_id, False)
        if btc_wallet:
            result[BlockchainType.BITCOIN.value] = btc_wallet.address

        # TON is supported in project - attempt generation
        try:
            ton_wallet, err = await WalletService.generate_ton_wallet(db, user_id, False)
            if ton_wallet:
                result[BlockchainType.TON.value] = ton_wallet.address
        except Exception:
            # not critical
            logger.debug("TON wallet generation skipped or failed")

        return result
