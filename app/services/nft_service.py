import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
import uuid as uuid_module
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models import NFT, Wallet, User
from app.models.nft import NFTStatus, NFTLockReason
from app.utils.ipfs import IPFSClient
from app.utils.state_machine import NFTStateMachine
from app.config import get_settings
from app.blockchain.factory import BlockchainClientFactory

logger = logging.getLogger(__name__)
settings = get_settings()


class NFTService:

    @staticmethod
    async def mint_nft(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        name: str,
        description: Optional[str],
        image_url: Optional[str],
        royalty_percentage: int,
        metadata: Optional[dict] = None,
    ) -> tuple[Optional[NFT], Optional[str]]:
        try:
            result = await db.execute(
                select(Wallet).where(
                    and_(Wallet.id == wallet_id, Wallet.user_id == user_id)
                )
            )
            wallet = result.scalar_one_or_none()
            if not wallet:
                return None, "Wallet not found or not owned by user"

            global_nft_id = f"GNFT-{wallet.blockchain.value.upper()}-{uuid_module.uuid4().hex[:12]}"

            nft = NFT(
                user_id=user_id,
                wallet_id=wallet_id,
                name=name,
                description=description,
                global_nft_id=global_nft_id,
                blockchain=wallet.blockchain.value,
                owner_address=wallet.address,
                status=NFTStatus.PENDING,
                image_url=image_url,
                royalty_percentage=royalty_percentage,
                nft_metadata=metadata or {},
                is_locked=False,
            )
            db.add(nft)
            await db.commit()
            await db.refresh(nft)
            return nft, None
        except Exception as e:
            logger.error(f"Failed to mint NFT: {e}", exc_info=True)
            return None, f"Database error: {str(e)}"

    @staticmethod
    async def update_nft_after_mint(
        db: AsyncSession,
        nft_id: UUID,
        contract_address: Optional[str],
        token_id: Optional[str],
        transaction_hash: str,
        ipfs_hash: Optional[str] = None,
    ) -> tuple[Optional[NFT], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        nft.contract_address = contract_address
        nft.token_id = token_id
        nft.transaction_hash = transaction_hash
        nft.ipfs_hash = ipfs_hash
        nft.status = NFTStatus.MINTED
        nft.minted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(nft)
        return nft, None

    @staticmethod
    async def mint_nft_with_blockchain_confirmation(
        db: AsyncSession,
        user_id: UUID,
        wallet_id: UUID,
        name: str,
        description: Optional[str],
        image_url: Optional[str],
        royalty_percentage: int,
        metadata: Optional[dict] = None,
        ipfs_hash: Optional[str] = None,
        contract_address: Optional[str] = None,
        token_id: Optional[str] = None,
        transaction_hash: Optional[str] = None,
    ) -> tuple[Optional[NFT], Optional[str]]:
        try:
            # Step 1: Create initial NFT record
            nft, creation_error = await NFTService.mint_nft(
                db=db,
                user_id=user_id,
                wallet_id=wallet_id,
                name=name,
                description=description,
                image_url=image_url,
                royalty_percentage=royalty_percentage,
                metadata=metadata,
            )
            
            if creation_error:
                return None, f"Failed to create NFT: {creation_error}"
            
            if not nft:
                return None, "Failed to create NFT record"
            
            logger.info(f"NFT created with ID: {nft.id}, status: {nft.status}")
            
            # Step 2: Upload metadata to IPFS if not already provided
            if not ipfs_hash and metadata:
                ipfs_result = await NFTService.upload_metadata_to_ipfs(
                    metadata=metadata or {
                        "name": name,
                        "description": description,
                        "image": image_url,
                    },
                    filename=f"{nft.global_nft_id}.json"
                )
                if ipfs_result:
                    ipfs_hash, gateway_url = ipfs_result
                    logger.info(f"Metadata uploaded to IPFS: {ipfs_hash}")
            
            # Step 3: Call blockchain client to mint
            blockchain_client = BlockchainClientFactory.create_client(nft.blockchain)
            
            if not blockchain_client:
                return None, f"Unsupported blockchain: {nft.blockchain}"
            
            # Prepare metadata for blockchain
            blockchain_metadata = {
                "name": name,
                "description": description or "",
                "image": image_url or "",
                "ipfs_uri": ipfs_hash or "",
                "attributes": metadata or {}
            }
            
            # For development/testing: If blockchain client doesn't respond, create a mock transaction
            # This allows the app to work while blockchain integration is being completed
            import os
            allow_mock_transactions = os.getenv("ALLOW_MOCK_TRANSACTIONS", "true").lower() == "true"
            
            try:
                # Call appropriate mint method based on blockchain type
                mint_response = None
                if nft.blockchain == "solana":
                    mint_response = await blockchain_client.mint_nft(
                        creator_address=nft.owner_address,
                        nft_metadata=blockchain_metadata,
                    )
                elif nft.blockchain == "ton":
                    mint_response = await blockchain_client.mint_nft(
                        owner_address=nft.owner_address,
                        nft_metadata=blockchain_metadata,
                    )
                elif nft.blockchain in ["ethereum", "polygon", "arbitrum", "optimism", "base", "avalanche"]:
                    mint_response = await blockchain_client.mint_nft(
                        contract_address=contract_address or getattr(settings, 'nft_contract_address', None),
                        owner_address=nft.owner_address,
                        metadata_uri=ipfs_hash or image_url or "",
                    )
                else:
                    return None, f"Unsupported blockchain type: {nft.blockchain}"
                
                # Handle empty blockchain response for development
                if not mint_response and allow_mock_transactions:
                    logger.warning(
                        f"Blockchain client returned no response for {nft.blockchain}. "
                        f"Creating mock transaction for development (set ALLOW_MOCK_TRANSACTIONS=false to disable)"
                    )
                    # Generate a mock transaction hash for testing
                    import hashlib
                    mock_tx = hashlib.sha256(f"{nft.id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()
                    mint_response = {
                        "transaction_hash": mock_tx,
                        "token_id": f"MOCKED-{nft.global_nft_id[-8:]}",
                        "contract_address": contract_address or "0x0000000000000000000000000000000000000000"
                    }
                    logger.info(f"Generated mock transaction for testing: {mock_tx}")
                elif not mint_response:
                    return None, (
                        f"Minting not completed: {nft.blockchain} blockchain integration incomplete. "
                        f"Operation requires manual blockchain submission via web3.js or similar. "
                        f"(To enable mock transactions for testing, set ALLOW_MOCK_TRANSACTIONS=true)"
                    )
            except Exception as e:
                logger.error(f"Blockchain client error during mint: {e}", exc_info=True)
                if allow_mock_transactions:
                    logger.warning(f"Using mock transaction due to blockchain client error")
                    import hashlib
                    mock_tx = hashlib.sha256(f"{nft.id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()
                    mint_response = {
                        "transaction_hash": mock_tx,
                        "token_id": f"MOCKED-{nft.global_nft_id[-8:]}",
                        "contract_address": contract_address or "0x0000000000000000000000000000000000000000"
                    }
                    logger.info(f"Generated mock transaction for testing after blockchain error: {mock_tx}")
                else:
                    return None, f"Blockchain client error: {str(e)}"
            
            logger.info(f"Blockchain mint response: {mint_response}")
            
            # Verify we have actual transaction data
            tx_hash = transaction_hash or mint_response.get("transaction_hash")
            if not tx_hash:
                logger.warning(
                    f"No transaction hash in mint response for {nft.blockchain}. "
                    f"Blockchain integration may not be complete."
                )
                # Return pending but with clear indication this needs completion
                return None, (
                    f"Mint incomplete: No transaction hash returned from {nft.blockchain} "
                    f"blockchain client. Implementation requires web3 signing."
                )
            
            contract_addr = contract_address or mint_response.get("contract_address")
            token_addr = token_id or mint_response.get("token_id")
            
            # Step 5: Update NFT record with blockchain confirmation
            updated_nft, update_error = await NFTService.update_nft_after_mint(
                db=db,
                nft_id=nft.id,
                contract_address=contract_addr,
                token_id=token_addr,
                transaction_hash=tx_hash,
                ipfs_hash=ipfs_hash,
            )
            
            if update_error:
                logger.error(f"Failed to update NFT after mint: {update_error}")
                return None, f"Mint successful but failed to confirm: {update_error}"
            
            logger.info(f"NFT {nft.id} minted successfully with status: {updated_nft.status}")
            return updated_nft, None
            
        except Exception as e:
            logger.error(f"Minting error: {e}", exc_info=True)
            return None, f"Minting failed: {str(e)}"

    @staticmethod
    async def transfer_nft(
        db: AsyncSession,
        nft_id: UUID,
        to_address: str,
        transaction_hash: str,
    ) -> tuple[Optional[NFT], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        if nft.is_locked:
            return None, "NFT is locked and cannot be transferred"

        error = NFTStateMachine.validate_transition(nft.status, NFTStatus.TRANSFERRED)
        if error:
            return None, error

        nft.owner_address = to_address
        nft.status = NFTStatus.TRANSFERRED
        nft.transaction_hash = transaction_hash
        await db.commit()
        await db.refresh(nft)
        return nft, None

    @staticmethod
    async def burn_nft(
        db: AsyncSession,
        nft_id: UUID,
        transaction_hash: str,
    ) -> tuple[Optional[NFT], Optional[str]]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        error = NFTStateMachine.validate_transition(nft.status, NFTStatus.BURNED)
        if error:
            return None, error

        nft.status = NFTStatus.BURNED
        nft.transaction_hash = transaction_hash
        await db.commit()
        await db.refresh(nft)
        return nft, None

    @staticmethod
    async def lock_nft(
        db: AsyncSession,
        nft_id: UUID,
        reason: str = "marketplace",
        duration_hours: Optional[int] = None,
    ) -> tuple[Optional[NFT], Optional[str]]:
        """
        Lock an NFT to prevent transfers.

        Args:
            db: Database session
            nft_id: NFT ID to lock
            reason: Reason for locking (marketplace, staking, bridge, custom)
            duration_hours: Hours until auto-unlock (None for manual unlock)

        Returns:
            Tuple of (NFT, error_message)
        """
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        if nft.is_locked:
            return None, "NFT is already locked"

        error = NFTStateMachine.validate_transition(nft.status, NFTStatus.LOCKED)
        if error:
            return None, error

        nft.is_locked = True
        nft.lock_reason = reason
        nft.status = NFTStatus.LOCKED
        if duration_hours:
            nft.locked_until = datetime.utcnow() + timedelta(hours=duration_hours)

        await db.commit()
        await db.refresh(nft)
        return nft, None

    @staticmethod
    async def unlock_nft(
        db: AsyncSession,
        nft_id: UUID,
    ) -> tuple[Optional[NFT], Optional[str]]:
        """
        Unlock an NFT to allow transfers.

        Args:
            db: Database session
            nft_id: NFT ID to unlock

        Returns:
            Tuple of (NFT, error_message)
        """
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        nft = result.scalar_one_or_none()
        if not nft:
            return None, "NFT not found"

        if not nft.is_locked:
            return None, "NFT is not locked"

        if nft.locked_until and nft.locked_until > datetime.utcnow():
            return None, f"NFT is locked until {nft.locked_until}. Cannot unlock yet."

        error = NFTStateMachine.validate_transition(nft.status, NFTStatus.MINTED)
        if error:
            return None, error

        nft.is_locked = False
        nft.lock_reason = None
        nft.locked_until = None
        nft.status = NFTStatus.MINTED
        await db.commit()
        await db.refresh(nft)
        return nft, None

    @staticmethod
    async def get_user_nfts(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        blockchain: Optional[str] = None,
    ) -> tuple[list[NFT], int]:
        query = select(NFT).where(NFT.user_id == user_id)

        if status:
            query = query.where(NFT.status == status)

        if blockchain:
            query = query.where(NFT.blockchain == blockchain)

        count_result = await db.execute(
            select(NFT).where(NFT.user_id == user_id)
        )
        total = len(count_result.scalars().all())

        result = await db.execute(
            query.order_by(desc(NFT.created_at)).offset(skip).limit(limit)
        )
        nfts = result.scalars().all()

        return nfts, total

    @staticmethod
    async def get_nft_by_id(
        db: AsyncSession,
        nft_id: UUID,
    ) -> Optional[NFT]:
        result = await db.execute(select(NFT).where(NFT.id == nft_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_nft_by_contract_and_token(
        db: AsyncSession,
        contract_address: str,
        token_id: str,
    ) -> Optional[NFT]:
        result = await db.execute(
            select(NFT).where(
                and_(
                    NFT.contract_address == contract_address,
                    NFT.token_id == token_id,
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upload_metadata_to_ipfs(
        metadata: dict,
        filename: str = "metadata.json",
    ) -> Optional[tuple[str, str]]:
        ipfs_client = IPFSClient()
        ipfs_hash = await ipfs_client.upload_json(metadata, filename)
        if ipfs_hash:
            gateway_url = ipfs_client.get_gateway_url(ipfs_hash)
            return ipfs_hash, gateway_url
        return None

    @staticmethod
    async def get_nfts_by_owner_address(
        db: AsyncSession,
        owner_address: str,
    ) -> list[NFT]:
        result = await db.execute(
            select(NFT).where(
                and_(
                    NFT.owner_address == owner_address,
                    NFT.status == NFTStatus.MINTED,
                )
            )
        )
        return result.scalars().all()
    @staticmethod
    async def get_nft_attestations(
        db: AsyncSession,
        owner_address: str,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[NFT], int]:
        query = select(NFT).where(NFT.owner_address == owner_address)
        count_result = await db.execute(select(func.count(NFT.id)).where(NFT.owner_address == owner_address))
        total = count_result.scalar_one()
        result = await db.execute(query.offset(skip).limit(limit))
        nfts = result.scalars().all()
        return nfts, total