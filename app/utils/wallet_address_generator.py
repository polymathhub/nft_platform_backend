import logging
import uuid
import hashlib
from app.models.wallet import BlockchainType

logger = logging.getLogger(__name__)


class WalletAddressGenerator:
    @staticmethod
    def generate_address(blockchain: BlockchainType) -> str:
        if isinstance(blockchain, str):
            blockchain = BlockchainType[blockchain.upper()]
        
        unique_id = str(uuid.uuid4()).replace('-', '')
        
        if blockchain in (BlockchainType.ETHEREUM, BlockchainType.POLYGON, 
                         BlockchainType.ARBITRUM, BlockchainType.OPTIMISM, 
                         BlockchainType.BASE, BlockchainType.AVALANCHE):
            return f"0x{unique_id[:40]}"
        
        elif blockchain == BlockchainType.SOLANA:
            return WalletAddressGenerator._generate_base58_address(unique_id, length=43)
        
        elif blockchain == BlockchainType.TON:
            return f"0:{unique_id[:47]}"
        
        elif blockchain == BlockchainType.BITCOIN:
            return f"1{WalletAddressGenerator._generate_base58_address(unique_id, length=33)}"
        
        else:
            return f"{blockchain.value[:3].upper()}_{unique_id[:30]}"

    @staticmethod
    def _generate_base58_address(source: str, length: int) -> str:
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        
        hash_bytes = hashlib.sha256(source.encode()).digest()
        
        result = ""
        num = int.from_bytes(hash_bytes, 'big')
        
        while num > 0 and len(result) < length:
            num, remainder = divmod(num, 58)
            result = alphabet[remainder] + result
        
        while len(result) < length:
            result = "1" + result
        
        return result[:length]

