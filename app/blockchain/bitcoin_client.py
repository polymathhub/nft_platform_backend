import logging
import aiohttp
from typing import Optional, Dict, Any, List
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BitcoinClient:
    def __init__(self, rpc_url: str = settings.bitcoin_rpc_url):
        self.rpc_url = rpc_url
        self.base_url = rpc_url.rstrip("/")

    async def get_address_balance(self, address: str) -> Optional[Dict[str, Any]]:
        # Get address balance and tx data
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/address/{address}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "confirmed_balance": data.get("chain_stats", {}).get("funded_txo_sum", 0),
                            "unconfirmed_balance": data.get("mempool_stats", {}).get("funded_txo_sum", 0),
                            "total_sent": data.get("chain_stats", {}).get("spent_txo_sum", 0),
                            "total_received": data.get("chain_stats", {}).get("funded_txo_sum", 0),
                            "tx_count": data.get("chain_stats", {}).get("tx_count", 0),
                            "unconfirmed_tx_count": data.get("mempool_stats", {}).get("tx_count", 0),
                        }
                    else:
                        logger.error(f"Bitcoin API error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin address query error: {e}")
            return None

    async def get_address_utxos(self, address: str) -> Optional[List[Dict[str, Any]]]:
        # Get unspent transaction outputs
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/address/{address}/utxo"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Bitcoin UTXO API error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin UTXO query error: {e}")
            return None

    async def get_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tx/{tx_id}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "txid": data.get("txid"),
                            "version": data.get("version"),
                            "locktime": data.get("locktime"),
                            "size": data.get("size"),
                            "weight": data.get("weight"),
                            "fee": data.get("fee"),
                            "inputs": data.get("vin"),
                            "outputs": data.get("vout"),
                            "status": data.get("status"),
                            "confirmed": data.get("status", {}).get("confirmed", False),
                            "block_height": data.get("status", {}).get("block_height"),
                            "block_time": data.get("status", {}).get("block_time"),
                        }
                    else:
                        logger.error(f"Bitcoin TX API error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin transaction query error: {e}")
            return None

    async def broadcast_transaction(self, tx_hex: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tx"
                async with session.post(url, data=tx_hex, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        error_text = await response.text()
                        logger.error(f"Bitcoin broadcast error: HTTP {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin broadcast error: {e}")
            return None

    async def get_fees(self) -> Optional[Dict[str, float]]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/fee-estimates"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        fees = await response.json()

                        # where key is confirmation count
                        return {
                            "fast": fees.get("1", 50),      # 1 block confirmation
                            "normal": fees.get("3", 30),    # 3 block confirmations
                            "slow": fees.get("6", 20),      # 6 block confirmations
                        }
                    else:
                        logger.error(f"Bitcoin fees API error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin fees query error: {e}")
            return None

    async def get_block_height(self) -> Optional[int]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/blocks/tip/height"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return int(await response.text())
                    else:
                        logger.error(f"Bitcoin block height error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin block height query error: {e}")
            return None

    async def get_mempool_stats(self) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/mempool"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Bitcoin mempool error: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Bitcoin mempool query error: {e}")
            return None
