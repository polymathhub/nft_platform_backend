import logging
from typing import Union
from app.models.wallet import BlockchainType
from app.blockchain.ton_client import TONClient
from app.blockchain.solana_client import SolanaClient
from app.blockchain.ethereum_client import EthereumClient
from app.blockchain.bitcoin_client import BitcoinClient
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BlockchainClientFactory:
    @staticmethod
    def create_client(blockchain: BlockchainType) -> Union[
        TONClient, SolanaClient, EthereumClient, BitcoinClient, None
    ]:
        # Create blockchain client for given type
        if blockchain == BlockchainType.TON:
            return TONClient(settings.ton_rpc_url)
        
        elif blockchain == BlockchainType.SOLANA:
            return SolanaClient(settings.solana_rpc_url)
        
        elif blockchain == BlockchainType.ETHEREUM:
            return EthereumClient(settings.ethereum_rpc_url)
        
        elif blockchain == BlockchainType.POLYGON:
            # Polygon uses Ethereum client with Polygon RPC URL
            return EthereumClient(settings.polygon_rpc_url)
        
        elif blockchain == BlockchainType.ARBITRUM:
            # Arbitrum uses Ethereum client with Arbitrum RPC URL
            return EthereumClient(settings.arbitrum_rpc_url)
        
        elif blockchain == BlockchainType.OPTIMISM:
            # Optimism uses Ethereum client with Optimism RPC URL
            return EthereumClient(settings.optimism_rpc_url)
        
        elif blockchain == BlockchainType.BASE:
            # Base uses Ethereum client with Base RPC URL
            return EthereumClient(settings.base_rpc_url)
        
        elif blockchain == BlockchainType.AVALANCHE:
            # Avalanche uses Ethereum client with Avalanche RPC URL
            return EthereumClient(settings.avalanche_rpc_url)
        
        elif blockchain == BlockchainType.BITCOIN:
            return BitcoinClient(settings.bitcoin_rpc_url)
        
        else:
            logger.warning(f"Unknown blockchain type: {blockchain}")
            return None

    @staticmethod
    async def get_wallet_balance(blockchain: BlockchainType, address: str) -> Union[float, str, dict, None]:
        client = BlockchainClientFactory.create_client(blockchain)
        if not client:
            return None

        try:
            if isinstance(client, BitcoinClient):
                return await client.get_address_balance(address)
            else:
                # TON, Solana, Ethereum and EVM-compatible chains balance return
                return await client.get_wallet_balance(address)
        except Exception as e:
            logger.error(f"Error getting balance for {blockchain}: {e}")
            return None
