"""
TON Blockchain Client - DEVELOPMENT MODE

⚠️ WARNING: This client provides MOCK IMPLEMENTATIONS for development/testing.

For production TON blockchain integration, you need to:
1. Install: pip install ton[full]
2. Implement real TON RPC calls
3. Add TON Connect signing support
4. Configure real TON wallet APIs

Current Implementation Status:
- get_wallet_balance(): ✓ Real RPC calls
- get_transaction_status(): ✓ Real RPC calls  
- get_contract_code(): ✓ Real RPC calls
- mint_nft(): ⚠️ MOCK - Returns mocked transaction
- transfer_nft(): ⚠️ STUBBED - Returns None

Environment Variable:
  - ALLOW_MOCK_TRANSACTIONS=true (default): Allow mock transactions for testing
  - ALLOW_MOCK_TRANSACTIONS=false: Reject mini implementations, require real blockchain

When ALLOW_MOCK_TRANSACTIONS is enabled, the service layer will:
1. Detect null/missing response from blockchain client
2. Log a warning
3. Generate a mock transaction for testing
4. Store it with "MOCKED-" prefix in token_id

This allows frontend testing without real blockchain operations.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TONClient:
    """
    TON Blockchain Client with mock implementations for development.
    
    To use with real TON blockchain:
    1. Implement ton.util for address validation
    2. Add TON Connect SDK integration for signing
    3. Use actual TON RPC endpoints
    4. Set ALLOW_MOCK_TRANSACTIONS=false to enforce real operations
    """
    
    def __init__(self, rpc_url: str = settings.ton_rpc_url):
        self.rpc_url = rpc_url
        self.workchain = settings.ton_workchain
        logger.info(f"TONClient initialized with RPC: {self.rpc_url}")

    async def get_wallet_balance(self, address: str) -> Optional[str]:
        """
        Query TON wallet balance via RPC.
        
        Returns:
            Balance in nanotons (optional)
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getAddressBalance",
                    "params": {"address": address},
                    "id": 1,
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    logger.error(f"TON RPC error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"TON balance query error: {e}")
            return None

    async def get_transaction_status(
        self,
        transaction_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Query TON transaction status via RPC.
        
        Returns:
            Transaction data dictionary (optional)
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getTransactionByHash",
                    "params": {"hash": transaction_hash},
                    "id": 1,
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    return None
        except Exception as e:
            logger.error(f"TON transaction query error: {e}")
            return None

    async def mint_nft(
        self,
        owner_address: str,
        nft_metadata: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        ⚠️ MOCK IMPLEMENTATION - Returns mocked NFT mint data.
        
        For production, implement real TON NFT minting:
        1. Use tonweb or ton.js SDK
        2. Create NFT collection contract
        3. Deploy via TON Connect
        4. Submit transaction to blockchain
        
        Args:
            owner_address: TON wallet address
            nft_metadata: NFT metadata (name, description, IPFS URI)
            
        Returns:
            Mocked transaction response or None
        """
        try:
            name = nft_metadata.get("name", "Untitled NFT")
            description = nft_metadata.get("description", "")
            content_uri = nft_metadata.get("ipfs_uri", "")
            
            logger.warning(
                f"⚠️ MOCK TON NFT MINT: Mock implementation for development. "
                f"Real TON SDK integration needed for production. "
                f"NFT: {name}, Owner: {owner_address}"
            )
            
            import hashlib
            import uuid
            from datetime import datetime
            
            # Generate mock transaction hash
            mock_tx = hashlib.sha256(
                f"{owner_address}-{name}-{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            # Return mock response structure matching expected format
            return {
                "transaction_hash": mock_tx,
                "token_id": f"TON-{uuid.uuid4().hex[:12]}",
                "contract_address": owner_address,
                "status": "pending",
                "owner_address": owner_address,
                "name": name,
                "description": description,
                "content_uri": content_uri,
                "message": "⚠️ MOCKED - TON mint transaction. Real blockchain signing required."
            }
        except Exception as e:
            logger.error(f"TON NFT mint error: {e}")
            return None

    async def transfer_nft(
        self,
        from_address: str,
        to_address: str,
        nft_address: str,
    ) -> Optional[str]:
        """
        ⚠️ STUBBED - NFT transfers not yet implemented.
        
        For production, implement:
        1. Build TON NFT transfer message
        2. Use TON Connect for user signing
        3. Send signed transaction to blockchain
        4. Return transaction hash
        
        Returns:
            None - requires full TON SDK implementation
        """
        try:
            logger.warning(
                f"⚠️ TON NFT TRANSFER STUBBED: "
                f"From: {from_address}, To: {to_address}, NFT: {nft_address}. "
                f"Full TON SDK implementation required for production."
            )
            
            if not from_address or not to_address or not nft_address:
                logger.error("Transfer requires valid addresses")
                return None
                
            logger.warning(
                "Transfer prepared but NOT submitted. "
                "Requires TON Connect signing and blockchain submission."
            )
            return None
            
        except Exception as e:
            logger.error(f"TON NFT transfer error: {e}", exc_info=True)
            return None

    async def get_contract_code(self, address: str) -> Optional[str]:
        """
        Query contract code hash from TON RPC.
        
        Returns:
            Code hash (optional)
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getAddressCodeHash",
                    "params": {"address": address},
                    "id": 1,
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    return None
        except Exception as e:
            logger.error(f"TON contract code query error: {e}")
            return None
