import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import User, Wallet
from app.models import Escrow
from app.models.wallet import BlockchainType, WalletType
from app.utils.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.config import get_settings
import os
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import serialization

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
                status="held",
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
        try:
            result = await db.execute(select(Escrow).where(Escrow.id == escrow_id))
            escrow = result.scalar_one_or_none()
            if not escrow:
                return None, "Escrow not found"
            escrow.status = "released"
            if tx_hash:
                escrow.tx_hash = tx_hash
            await db.commit()
            await db.refresh(escrow)
            return escrow, None
        except Exception as e:
            logger.error(f"Failed to release escrow: {e}")
            return None, str(e)

    # ------------------ Wallet generation helpers ------------------
    @staticmethod
    async def generate_evm_wallet(
        db: AsyncSession,
        user_id: UUID,
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a single EVM wallet (shared across EVM-compatible chains).

        Uses SECP256K1 private key and Keccak-256 for address derivation.
        Requires a keccak implementation (pysha3) available as `sha3` or
        Crypto.Hash.keccak. Encrypted private key is stored using existing
        `encrypt_sensitive_data` and `mnemonic_encryption_key`.
        """
        # Idempotent: if user already has an EVM wallet, return it
        existing = await WalletService.get_user_wallets(db, user_id, BlockchainType.ETHEREUM)
        if existing:
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

        # Create wallet record (one record represents EVM family)
        wallet, err = await WalletService.create_wallet(
            db=db,
            user_id=user_id,
            blockchain=BlockchainType.ETHEREUM,
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
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate an Ed25519 keypair for Solana and store encrypted private key.

        Uses base58 encoding for the public key/address. A small internal
        base58 encoder is included to avoid adding external deps.
        """
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
            blockchain=BlockchainType.SOLANA,
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
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a Bitcoin P2PKH address (base58check) using secp256k1.

        This implementation creates a compressed public key and P2PKH address.
        It relies on hashlib supporting RIPEMD160; if not available, it will
        raise an informative error.
        """
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
            blockchain=BlockchainType.BITCOIN,
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
        make_primary: bool = False,
    ) -> tuple[Optional[Wallet], Optional[str]]:
        """Generate a TON wallet keypair (Ed25519) and store encrypted key.

        TON address encoding differs from Solana; for now store public key
        base64 as the address and set metadata.workchain when available.
        """
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
            blockchain=BlockchainType.TON,
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
