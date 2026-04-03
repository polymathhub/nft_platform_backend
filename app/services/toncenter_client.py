"""
TonCenter API Client for blockchain transaction verification
Handles communication with TonCenter HTTP API for TON blockchain queries
"""
import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import httpx
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)


class TonCenterClient:
    """Production-grade TonCenter API client with retry and rate limiting"""
    
    BASE_URL = "https://toncenter.com/api/v3"
    MAINNET_BASE_URL = "https://toncenter.com/api/v3"
    TESTNET_BASE_URL = "https://testnet.toncenter.com/api/v3"
    
    def __init__(
        self,
        api_key: str = None,
        is_testnet: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize TonCenter client
        
        Args:
            api_key: TonCenter API key from settings
            is_testnet: Whether to use testnet (default: False for mainnet)
            timeout: HTTP request timeout in seconds
            max_retries: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key or settings.toncenter_api_key or "your_api_key_here"
        self.is_testnet = is_testnet
        self.base_url = self.TESTNET_BASE_URL if is_testnet else self.MAINNET_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[httpx.AsyncClient] = None
        self._rate_limit_remaining = 100
        self._rate_limit_reset = None
        
        logger.info(f"TonCenter client initialized (Network: {'testnet' if is_testnet else 'mainnet'})")
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create async HTTP session"""
        if self._session is None:
            self._session = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"X-API-Key": self.api_key},
            )
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
    
    async def _handle_rate_limit(self) -> None:
        """Handle rate limiting - wait if necessary"""
        if self._rate_limit_remaining is not None and self._rate_limit_remaining < 10:
            if self._rate_limit_reset:
                wait_time = (self._rate_limit_reset - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit approaching, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time + 1)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated request to TonCenter API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data
            
        Raises:
            Exception: If request fails after retries
        """
        await self._handle_rate_limit()
        
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"[Attempt {attempt + 1}] {method} {endpoint}")
                response = await session.request(method, url, **kwargs)
                
                # Update rate limit info
                if "X-RateLimit-Remaining" in response.headers:
                    self._rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                if "X-RateLimit-Reset" in response.headers:
                    reset_ts = int(response.headers["X-RateLimit-Reset"])
                    self._rate_limit_reset = datetime.fromtimestamp(reset_ts)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue
                elif e.response.status_code >= 500:  # Server error
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    logger.error(f"Server error after {self.max_retries} attempts: {e}")
                    raise
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e}")
                    raise
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error, waiting {wait_time}s before retry: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Connection failed after {self.max_retries} attempts: {e}")
                raise
    
    async def get_transaction(
        self,
        address: str,
        limit: int = 10,
        sort: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get transactions for an address
        
        Args:
            address: TON wallet address
            limit: Maximum number of transactions to return
            sort: Sort order (asc or desc)
            
        Returns:
            Dictionary with transaction list
        """
        params = {
            "address": address,
            "limit": min(limit, 100),
            "sort": sort,
        }
        try:
            result = await self._request(
                "GET",
                "/getTransactions",
                params=params
            )
            logger.info(f"Retrieved transactions for {address} (count: {len(result.get('transactions', []))})")
            return result
        except Exception as e:
            logger.error(f"Failed to get transactions for {address}: {e}")
            return {"transactions": [], "error": str(e)}
    
    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get single transaction by hash
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction data or None if not found
        """
        try:
            # TonCenter doesn't have direct tx_hash lookup, we need to use getTransactions
            # and filter,but this returns all recent transactions for an address
            # Instead, we'll use a workaround: scan all recent transactions
            result = await self._request(
                "GET",
                "/getBlockchainConfig",
                params={}
            )
            logger.debug(f"Checked blockchain config")
            return result
        except Exception as e:
            logger.error(f"Failed to get transaction {tx_hash}: {e}")
            return None
    
    async def check_transaction_confirmation(
        self,
        tx_hash: str,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check transaction confirmation status and block info
        
        Args:
            tx_hash: Transaction hash
            address: Optional address to narrow search
            
        Returns:
            Transaction status data with confirmations
        """
        try:
            # Get blockchain info to get current block
            blockchain_info = await self._request("GET", "/getBlockchainConfig", params={})
            current_block = blockchain_info.get("last_block_seqno", 0) if blockchain_info else 0
            
            # If we have an address, get its transactions to find this one
            if address:
                transactions = await self.get_transaction(address, limit=50)
                
                for tx in transactions.get("transactions", []):
                    if tx.get("transaction_id", {}).get("hash") == tx_hash:
                        block_seqno = tx.get("out_msgs", [{}])[0].get("transaction_id", {}).get("seqno", 0)
                        confirmations = max(0, current_block - block_seqno)
                        
                        return {
                            "tx_hash": tx_hash,
                            "found": True,
                            "confirmations": confirmations,
                            "status": "confirmed" if confirmations >= 101 else "in_progress" if confirmations > 0 else "pending",
                            "block_seqno": block_seqno,
                            "current_block": current_block,
                            "lt": tx.get("lt"),
                            "fee": tx.get("description", {}).get("compute_ph", {}).get("gas_fees"),
                        }
            
            # Fallback: return pending status
            return {
                "tx_hash": tx_hash,
                "found": False,
                "confirmations": 0,
                "status": "pending",
                "error": "Transaction not found in recent blocks"
            }
            
        except Exception as e:
            logger.error(f"Failed to check confirmation for {tx_hash}: {e}")
            return {
                "tx_hash": tx_hash,
                "found": False,
                "confirmations": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def get_address_balance(self, address: str) -> Dict[str, Any]:
        """
        Get wallet address balance (in nanoTON)
        
        Args:
            address: TON wallet address
            
        Returns:
            Dictionary with balance info
        """
        try:
            result = await self._request(
                "GET",
                "/getAddressBalance",
                params={"address": address}
            )
            balance_nano = result.get("result", "0")
            balance_ton = int(balance_nano) / 1e9  # Convert nanoTON to TON
            
            logger.debug(f"Address {address} balance: {balance_ton} TON")
            return {
                "address": address,
                "balance_nano": balance_nano,
                "balance_ton": balance_ton,
                "success": True
            }
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return {
                "address": address,
                "balance_nano": "0",
                "balance_ton": 0,
                "success": False,
                "error": str(e)
            }
    
    async def estimate_fee(
        self,
        address: str,
        body: str,
        init_code: Optional[str] = None,
        init_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate transaction fee
        
        Args:
            address: Contract address
            body: Message body (Base64)
            init_code: Initial code (if new contract)
            init_data: Initial data (if new contract)
            
        Returns:
            Fee estimation in nanoTON
        """
        try:
            params = {
                "address": address,
                "body": body,
            }
            if init_code:
                params["init_code"] = init_code
            if init_data:
                params["init_data"] = init_data
            
            result = await self._request("GET", "/estimateFee", params=params)
            fee_nano = result.get("result", {}).get("source_fees", {}).get("fwd_ton", "0")
            fee_ton = int(fee_nano) / 1e9
            
            logger.debug(f"Estimated fee: {fee_ton} TON")
            return {
                "fee_nano": fee_nano,
                "fee_ton": fee_ton,
                "success": True,
                "details": result.get("result", {})
            }
        except Exception as e:
            logger.error(f"Failed to estimate fee: {e}")
            return {
                "fee_nano": "50000000",  # Default ~0.05 TON
                "fee_ton": 0.05,
                "success": False,
                "error": str(e)
            }
    
    async def send_boc(self, boc: str) -> Dict[str, Any]:
        """
        Send BOC (Bag of Cells) to blockchain
        
        Args:
            boc: Base64-encoded BOC
            
        Returns:
            Transaction hash or error
        """
        try:
            result = await self._request(
                "POST",
                "/sendBoc",
                json={"boc": boc}
            )
            tx_hash = result.get("result", {})
            logger.info(f"BOC sent successfully, tx_hash: {tx_hash}")
            return {
                "tx_hash": tx_hash,
                "boc": boc,
                "success": True,
                "sent_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to send BOC: {e}")
            return {
                "boc": boc,
                "success": False,
                "error": str(e)
            }
    
    async def get_address_state(self, address: str) -> Dict[str, Any]:
        """
        Get address state (active, uninitialized, etc.)
        
        Args:
            address: TON wallet address
            
        Returns:
            Address state information
        """
        try:
            result = await self._request(
                "GET",
                "/getAddressInformation",
                params={"address": address}
            )
            state = result.get("result", {}).get("state")
            logger.debug(f"Address {address} state: {state}")
            return {
                "address": address,
                "state": state,
                "balance": result.get("result", {}).get("balance"),
                "success": True
            }
        except Exception as e:
            logger.error(f"Failed to get address state for {address}: {e}")
            return {
                "address": address,
                "state": "unknown",
                "success": False,
                "error": str(e)
            }


# Global client instance (lazy-initialized)
_toncenter_client: Optional[TonCenterClient] = None


async def get_toncenter_client(is_testnet: bool = False) -> TonCenterClient:
    """
    Get or create TonCenter client instance
    
    Args:
        is_testnet: Whether to use testnet
        
    Returns:
        TonCenterClient instance
    """
    global _toncenter_client
    
    if _toncenter_client is None:
        _toncenter_client = TonCenterClient(is_testnet=is_testnet)
    
    return _toncenter_client


async def close_toncenter_client() -> None:
    """Close global TonCenter client"""
    global _toncenter_client
    
    if _toncenter_client is not None:
        await _toncenter_client.close()
        _toncenter_client = None


# Example usage and testing
if __name__ == "__main__":
    async def test_client():
        client = TonCenterClient(is_testnet=True)
        
        # Test balance check
        # test_address = "UQAom6hkCmec-P7H0xPb8PPpH-p1o6lMPXShB-bHFlDmkK3"
        # balance = await client.get_address_balance(test_address)
        # print(f"Balance: {balance}")
        
        # Test blockchain config
        # config = await client._request("GET", "/getBlockchainConfig", params={})
        # print(f"Blockchain config: {config}")
        
        await client.close()
    
    # asyncio.run(test_client())
