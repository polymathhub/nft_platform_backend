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
        if blockchain == BlockchainType.TON:
            return TONClient(settings.ton_rpc_url)
        elif blockchain == BlockchainType.SOLANA:
            return SolanaClient(settings.solana_rpc_url)
        elif blockchain == BlockchainType.ETHEREUM:
            return EthereumClient(settings.ethereum_rpc_url)
        elif blockchain == BlockchainType.POLYGON:
            return EthereumClient(settings.polygon_rpc_url)
        elif blockchain == BlockchainType.ARBITRUM:
            return EthereumClient(settings.arbitrum_rpc_url)
        elif blockchain == BlockchainType.OPTIMISM:
            return EthereumClient(settings.optimism_rpc_url)
        elif blockchain == BlockchainType.BASE:
            return EthereumClient(settings.base_rpc_url)
        elif blockchain == BlockchainType.AVALANCHE:
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
                return await client.get_wallet_balance(address)
        except Exception as e:
            logger.error(f"Error getting balance for {blockchain}: {e}")
            return None
