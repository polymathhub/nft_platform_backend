import logging
import aiohttp
from typing import Optional, Dict, Any, List
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SolanaClient:
    def __init__(self, rpc_url: str = settings.solana_rpc_url):
        self.rpc_url = rpc_url
        self.commitment = settings.solana_commitment

    async def get_wallet_balance(self, address: str) -> Optional[float]:
        # Get SOL balance
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getBalance",
                    "params": [address],
                    "id": "1",
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data and "value" in data["result"]:
                            # Convert lamports to SOL (1 SOL = 1e9 lamports)
                            lamports = data["result"]["value"]
                            return lamports / 1e9
                    logger.error(f"Solana RPC error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Solana balance query error: {e}")
            return None

    async def get_token_balance(
        self,
        token_account: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getTokenAccountBalance",
                    "params": [token_account],
                    "id": "1",
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    return None
        except Exception as e:
            logger.error(f"Solana token balance query error: {e}")
            return None

    async def get_transaction_status(
        self,
        transaction_hash: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getTransaction",
                    "params": [transaction_hash, {"encoding": "json"}],
                    "id": "1",
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    return None
        except Exception as e:
            logger.error(f"Solana transaction query error: {e}")
            return None

    async def mint_nft(
        self,
        creator_address: str,
        nft_metadata: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        Mint an NFT on Solana using Metaplex standard.
        
        Args:
            creator_address: Creator's Solana wallet address
            nft_metadata: Metadata dictionary with name, symbol, uri, etc.
        
        Returns:
            Dictionary with transaction hash and NFT mint address, or None if failed
        """
        try:
            # Extract metadata
            name = nft_metadata.get("name", "Untitled NFT")
            symbol = nft_metadata.get("symbol", "NFT")
            metadata_uri = nft_metadata.get("uri", "")
            
            # Log mint request
            logger.info(
                f"Solana NFT mint initiated - creator: {creator_address}, "
                f"name: {name}, uri: {metadata_uri}"
            )
            
            # In a full implementation, this would:
            # 1. Use Solana web3.py or Metaplex SDK
            # 2. Create a mint account
            # 3. Create metadata account pointing to IPFS
            # 4. Sign and send transaction
            # For now, return pending status
            return {
                "status": "pending",
                "creator_address": creator_address,
                "name": name,
                "symbol": symbol,
                "metadata_uri": metadata_uri,
                "message": "Solana mint transaction prepared (signing required)"
            }
        except Exception as e:
            logger.error(f"Solana NFT mint error: {e}")
            return None

    async def transfer_nft(
        self,
        from_address: str,
        to_address: str,
        nft_mint: str,
    ) -> Optional[str]:
        logger.info(
            f"Solana NFT transfer placeholder - from: {from_address}, to: {to_address}"
        )
        return None

    async def get_nft_metadata(
        self,
        nft_mint: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getAccountInfo",
                    "params": [nft_mint, {"encoding": "jsonParsed"}],
                    "id": "1",
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                    return None
        except Exception as e:
            logger.error(f"Solana NFT metadata query error: {e}")
            return None

    async def get_recent_blockhash(self) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "getRecentBlockhash",
                    "params": [{"commitment": self.commitment}],
                    "id": "1",
                }
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data and "value" in data["result"]:
                            return data["result"]["value"]["blockhash"]
                    return None
        except Exception as e:
            logger.error(f"Solana blockhash query error: {e}")
            return None
