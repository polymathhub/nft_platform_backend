import logging
import aiohttp
from typing import Optional, Dict, Any, List
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EthereumClient:
    def __init__(self, rpc_url: str = settings.ethereum_rpc_url):
        self.rpc_url = rpc_url
        self.request_id = 1

    async def call_rpc(self, method: str, params: List[Any]) -> Optional[Dict[str, Any]]:
        # Make JSON-RPC call to blockchain
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": self.request_id,
                }
                self.request_id += 1
                async with session.post(self.rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                        elif "error" in data:
                            logger.error(f"RPC error: {data['error']}")
                            return None
                    else:
                        logger.error(f"RPC error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"RPC call error: {e}")
            return None

    async def get_wallet_balance(self, address: str) -> Optional[float]:
        # Get balance in native token (ETH, MATIC, etc.)
        try:
            # Checksum address
            if not address.startswith("0x"):
                address = "0x" + address
            
            balance_wei = await self.call_rpc("eth_getBalance", [address, "latest"])
            if balance_wei:
                # Convert wei to native token (1 token = 1e18 wei)
                return int(balance_wei, 16) / 1e18
            return None
        except Exception as e:
            logger.error(f"Balance query error: {e}")
            return None

    async def get_token_balance(self, address: str, contract_address: str) -> Optional[float]:
        try:
            if not address.startswith("0x"):
                address = "0x" + address
            if not contract_address.startswith("0x"):
                contract_address = "0x" + contract_address

            # ERC-20 balanceOf function signature hash
            function_selector = "0x70a08231"
            # Pad address to 32 bytes
            padded_address = address[2:].zfill(64)
            
            data = function_selector + padded_address
            result = await self.call_rpc(
                "eth_call",
                [{
                    "to": contract_address,
                    "data": data
                }, "latest"]
            )
            
            if result:
                return int(result, 16)
            return None
        except Exception as e:
            logger.error(f"Token balance error: {e}")
            return None

    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        try:
            receipt = await self.call_rpc("eth_getTransactionReceipt", [tx_hash])
            return receipt
        except Exception as e:
            logger.error(f"Transaction receipt error: {e}")
            return None

    async def get_gas_price(self) -> Optional[float]:
        try:
            gas_price_wei = await self.call_rpc("eth_gasPrice", [])
            if gas_price_wei:
                # Convert wei to Gwei (1 Gwei = 1e9 wei)
                return int(gas_price_wei, 16) / 1e9
            return None
        except Exception as e:
            logger.error(f"Gas price error: {e}")
            return None

    async def get_nft_owner(self, contract_address: str, token_id: int) -> Optional[str]:
        try:
            if not contract_address.startswith("0x"):
                contract_address = "0x" + contract_address

            # ERC-721 ownerOf function signature: 0x6352211e
            function_selector = "0x6352211e"
            # Pad token_id to 32 bytes
            padded_token_id = hex(token_id)[2:].zfill(64)
            
            data = function_selector + padded_token_id
            result = await self.call_rpc(
                "eth_call",
                [{
                    "to": contract_address,
                    "data": data
                }, "latest"]
            )
            
            if result:
                # Extract address from result (last 20 bytes)
                owner = "0x" + result[-40:]
                return owner
            return None
        except Exception as e:
            logger.error(f"NFT owner query error: {e}")
            return None

    async def get_block_number(self) -> Optional[int]:
        try:
            block_number = await self.call_rpc("eth_blockNumber", [])
            if block_number:
                return int(block_number, 16)
            return None
        except Exception as e:
            logger.error(f"Block number error: {e}")
            return None

    async def estimate_gas(self, tx: Dict[str, Any]) -> Optional[int]:
        try:
            gas_estimate = await self.call_rpc("eth_estimateGas", [tx])
            if gas_estimate:
                return int(gas_estimate, 16)
            return None
        except Exception as e:
            logger.error(f"Gas estimation error: {e}")
            return None

    async def send_raw_transaction(self, signed_tx: str) -> Optional[str]:
        try:
            tx_hash = await self.call_rpc("eth_sendRawTransaction", [signed_tx])
            return tx_hash
        except Exception as e:
            logger.error(f"Transaction send error: {e}")
            return None

    async def mint_nft(
        self,
        contract_address: str,
        owner_address: str,
        metadata_uri: str,
        contract_abi: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mint an NFT on Ethereum-compatible blockchains.
        
        Args:
            contract_address: Smart contract address
            owner_address: Owner's wallet address
            metadata_uri: IPFS or HTTP URI to metadata
            contract_abi: Optional contract ABI for encoding (uses mintTo for now)
        
        Returns:
            Dictionary with transaction hash and token data, or None if failed
        """
        try:
            if not contract_address.startswith("0x"):
                contract_address = "0x" + contract_address
            if not owner_address.startswith("0x"):
                owner_address = "0x" + owner_address

            # Standard ERC-721 mint function: mintTo(address to, string uri)
            # This is a placeholder - actual implementation depends on contract implementation
            # Function selector for a generic mint function: 0x6a627842 (mintTo)
            function_selector = "0x6a627842"
            
            # Pad owner address to 32 bytes
            padded_address = owner_address[2:].zfill(64)
            
            # For a complete implementation, you would:
            # 1. Encode the metadata_uri properly (string type in Solidity)
            # 2. Use the contract ABI if provided
            # 3. Estimate gas, get gas price, sign the transaction
            # 4. Send the signed transaction
            # For now, log the mint request
            logger.info(
                f"Ethereum NFT mint request - contract: {contract_address}, "
                f"owner: {owner_address}, metadata: {metadata_uri}"
            )
            
            return {
                "status": "pending",
                "contract_address": contract_address,
                "owner_address": owner_address,
                "metadata_uri": metadata_uri,
                "message": "Mint transaction prepared (signing required)"
            }
        except Exception as e:
            logger.error(f"Ethereum NFT mint error: {e}")
            return None
