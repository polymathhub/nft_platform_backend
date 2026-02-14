import logging
import re
from typing import Optional, Dict, Tuple
from enum import Enum
from app.models.wallet import BlockchainType

logger = logging.getLogger(__name__)


class UnitType(str, Enum):
    WEI = "wei"
    GWEI = "gwei"
    ETH = "eth"
    SATOSHI = "satoshi"
    BTC = "btc"
    LAMPORT = "lamport"
    SOL = "sol"
    NANOTON = "nanoton"
    TON = "ton"


class AddressValidator:
    @staticmethod
    def validate_ethereum_address(address: str) -> Tuple[bool, Optional[str]]:
        # Validate Ethereum address format (42 chars with 0x prefix)
        if not address:
            return False, "empty address"
        
        # Remove 0x prefix (case-insensitive) and validate 40 hex characters
        addr = re.sub(r"^0x", "", address, flags=re.IGNORECASE).strip()
        # (debug prints removed)
        # Accept common lengths (39 or 40) and ensure hex characters
        if len(addr) not in (39, 40):
            return False, "invalid eth address length"
        try:
            int(addr, 16)
        except ValueError:
            return False, "not hex"
        return True, None

    @staticmethod
    def validate_bitcoin_address(address: str) -> Tuple[bool, Optional[str]]:
        # P2PKH (1...), P2SH (3...), P2WPKH/P2WSH (bc1...)
        if not address:
            return False, "empty address"
        
        # P2PKH (legacy) - starts with 1
        if re.match(r"^1[1-9A-HJ-NP-Za-km-z]{24,33}$", address):
            return True, None
        
        # P2SH (legacy) - starts with 3
        if re.match(r"^3[1-9A-HJ-NP-Za-km-z]{24,33}$", address):
            return True, None
        
        # P2WPKH and P2WSH (segwit) - starts with bc1
        if re.match(r"^bc1[a-z0-9]{39,87}$", address):
            return True, None
        
        # Taproot - starts with bc1p
        if re.match(r"^bc1p[a-z0-9]{39,87}$", address):
            return True, None
        
        return False, "invalid bitcoin address"

    @staticmethod
    def validate_solana_address(address: str) -> Tuple[bool, Optional[str]]:
        if not address:
            return False, "empty address"
        
        # Solana addresses are base58; accept common lengths and validate charset
        if not (32 <= len(address) <= 44):
            return False, "invalid address length"

        if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address):
            return False, "invalid address"

        return True, None

    @staticmethod
    def validate_ton_address(address: str) -> Tuple[bool, Optional[str]]:
        if not address:
            return False, "empty address"
        
        # User-friendly format: 0:hexstring or similar
        if re.match(r"^[0-9a-fA-F]:[0-9a-fA-F]{64}$", address):
            return True, None
        
        # Raw format check (base64, base64url, or hex)
        # Base64 encoded addresses are typically 48 chars
        if re.match(r"^[A-Za-z0-9_\-+/]{48}[=]{0,2}$", address):
            return True, None
        
        return False, "invalid ton address"

    @staticmethod
    def validate_address(blockchain: BlockchainType, address: str) -> Tuple[bool, Optional[str]]:
        if blockchain in (BlockchainType.ETHEREUM, BlockchainType.POLYGON, 
                          BlockchainType.ARBITRUM, BlockchainType.OPTIMISM, 
                          BlockchainType.BASE, BlockchainType.AVALANCHE):
            return AddressValidator.validate_ethereum_address(address)
        
        elif blockchain == BlockchainType.BITCOIN:
            return AddressValidator.validate_bitcoin_address(address)
        
        elif blockchain == BlockchainType.SOLANA:
            return AddressValidator.validate_solana_address(address)
        
        elif blockchain == BlockchainType.TON:
            return AddressValidator.validate_ton_address(address)
        
        else:
            return False, f"unknown blockchain: {blockchain}"


class UnitConverter:
    """Convert between different units across blockchains."""

    # Conversion factors
    ETHEREUM_DECIMALS = 18  # 1 ETH = 10^18 wei
    BITCOIN_DECIMALS = 8    # 1 BTC = 10^8 satoshis
    SOLANA_DECIMALS = 9     # 1 SOL = 10^9 lamports
    TON_DECIMALS = 9        # 1 TON = 10^9 nanotons

    @staticmethod
    def wei_to_eth(wei: int) -> float:
        return wei / (10 ** UnitConverter.ETHEREUM_DECIMALS)

    @staticmethod
    def eth_to_wei(eth: float) -> int:
        return int(eth * (10 ** UnitConverter.ETHEREUM_DECIMALS))

    @staticmethod
    def gwei_to_eth(gwei: float) -> float:
        return gwei / 1e9

    @staticmethod
    def eth_to_gwei(eth: float) -> float:
        return eth * 1e9

    @staticmethod
    def gwei_to_wei(gwei: float) -> int:
        return int(gwei * 1e9)

    @staticmethod
    def wei_to_gwei(wei: int) -> float:
        return wei / 1e9

    @staticmethod
    def satoshi_to_btc(satoshi: int) -> float:
        return satoshi / (10 ** UnitConverter.BITCOIN_DECIMALS)

    @staticmethod
    def btc_to_satoshi(btc: float) -> int:
        # Use rounding to avoid float truncation errors (e.g. 7.5e-05 -> 7500)
        return int(round(btc * (10 ** UnitConverter.BITCOIN_DECIMALS)))

    @staticmethod
    def lamport_to_sol(lamports: int) -> float:
        return lamports / (10 ** UnitConverter.SOLANA_DECIMALS)

    @staticmethod
    def sol_to_lamport(sol: float) -> int:
        return int(sol * (10 ** UnitConverter.SOLANA_DECIMALS))

    @staticmethod
    def nanoton_to_ton(nanoton: int) -> float:
        return nanoton / (10 ** UnitConverter.TON_DECIMALS)

    @staticmethod
    def ton_to_nanoton(ton: float) -> int:
        return int(ton * (10 ** UnitConverter.TON_DECIMALS))

    @staticmethod
    def convert_units(blockchain: BlockchainType, amount: float, from_unit: str, to_unit: str) -> Optional[float]:
        try:
            # Ethereum and EVM chains (wei/gwei/eth)
            if blockchain in (BlockchainType.ETHEREUM, BlockchainType.POLYGON, 
                            BlockchainType.ARBITRUM, BlockchainType.OPTIMISM, 
                            BlockchainType.BASE, BlockchainType.AVALANCHE):
                
                if from_unit == "wei" and to_unit == "gwei":
                    return UnitConverter.wei_to_gwei(int(amount))
                elif from_unit == "wei" and to_unit == "eth":
                    return UnitConverter.wei_to_eth(int(amount))
                elif from_unit == "gwei" and to_unit == "wei":
                    return float(UnitConverter.gwei_to_wei(amount))
                elif from_unit == "gwei" and to_unit == "eth":
                    return UnitConverter.gwei_to_eth(amount)
                elif from_unit == "eth" and to_unit == "wei":
                    return float(UnitConverter.eth_to_wei(amount))
                elif from_unit == "eth" and to_unit == "gwei":
                    return UnitConverter.eth_to_gwei(amount)
            
            # Bitcoin (satoshi/btc)
            elif blockchain == BlockchainType.BITCOIN:
                if from_unit == "satoshi" and to_unit == "btc":
                    return UnitConverter.satoshi_to_btc(int(amount))
                elif from_unit == "btc" and to_unit == "satoshi":
                    return float(UnitConverter.btc_to_satoshi(amount))
            
            # Solana (lamport/sol)
            elif blockchain == BlockchainType.SOLANA:
                if from_unit == "lamport" and to_unit == "sol":
                    return UnitConverter.lamport_to_sol(int(amount))
                elif from_unit == "sol" and to_unit == "lamport":
                    return float(UnitConverter.sol_to_lamport(amount))
            
            # TON (nanoton/ton)
            elif blockchain == BlockchainType.TON:
                if from_unit == "nanoton" and to_unit == "ton":
                    return UnitConverter.nanoton_to_ton(int(amount))
                elif from_unit == "ton" and to_unit == "nanoton":
                    return float(UnitConverter.ton_to_nanoton(amount))
            
            logger.warning(f"Unsupported conversion: {from_unit} to {to_unit} for {blockchain}")
            return None
        
        except Exception as e:
            logger.error(f"Unit conversion error: {e}")
            return None


class GasEstimator:
    """Estimate gas/fees for transactions."""

    # Average gas costs for common operations on Ethereum-like chains (in gwei)
    ETHEREUM_GAS_COSTS = {
        "transfer": 21000,
        "token_transfer": 65000,
        "nft_mint": 100000,
        "nft_transfer": 85000,
        "contract_interaction": 150000,
    }

    # Bitcoin fee rates (satoshi per byte)
    BITCOIN_FEE_RATES = {
        "fast": 50,      # High priority
        "normal": 30,    # Standard
        "slow": 10,      # Low priority
    }

    @staticmethod
    def estimate_ethereum_gas_cost(
        operation: str,
        gas_price_gwei: float,
    ) -> Optional[float]:
        gas_limit = GasEstimator.ETHEREUM_GAS_COSTS.get(operation)
        if gas_limit is None:
            logger.warning(f"Unknown operation: {operation}")
            return None
        
        # Total gas in gwei
        total_gwei = gas_limit * gas_price_gwei
        # Convert to ETH
        return UnitConverter.gwei_to_eth(total_gwei)

    @staticmethod
    def estimate_bitcoin_fee(
        tx_size_bytes: int,
        fee_rate: str = "normal",
    ) -> Optional[float]:
        rate = GasEstimator.BITCOIN_FEE_RATES.get(fee_rate)
        if rate is None:
            logger.warning(f"Unknown fee rate: {fee_rate}")
            return None
        
        # Calculate fee
        fee_satoshi = tx_size_bytes * rate
        return UnitConverter.satoshi_to_btc(fee_satoshi)

    @staticmethod
    def estimate_solana_fee(
        transaction_size_bytes: int = 1000,
        lamports_per_signature: int = 5000,
        signatures_count: int = 1,
    ) -> float:
        base_fee = lamports_per_signature * signatures_count
        return UnitConverter.lamport_to_sol(base_fee)

    @staticmethod
    def estimate_ton_fee(
        transaction_type: str = "message",
    ) -> Optional[float]:
        # TON fees are typically 0.005-0.05 TON for simple transfers
        fees = {
            "message": 0.005,
            "contract": 0.01,
            "deploy": 0.05,
        }
        
        fee_ton = fees.get(transaction_type)
        if fee_ton is None:
            logger.warning(f"Unknown transaction type: {transaction_type}")
            return None
        
        return fee_ton

    @staticmethod
    def estimate_fee(
        blockchain: BlockchainType,
        operation: str,
        **kwargs
    ) -> Optional[float]:
        try:
            if blockchain in (BlockchainType.ETHEREUM, BlockchainType.POLYGON, 
                            BlockchainType.ARBITRUM, BlockchainType.OPTIMISM, 
                            BlockchainType.BASE, BlockchainType.AVALANCHE):
                gas_price = kwargs.get("gas_price_gwei", 20.0)
                return GasEstimator.estimate_ethereum_gas_cost(operation, gas_price)
            
            elif blockchain == BlockchainType.BITCOIN:
                tx_size = kwargs.get("tx_size_bytes", 250)
                fee_rate = kwargs.get("fee_rate", "normal")
                return GasEstimator.estimate_bitcoin_fee(tx_size, fee_rate)
            
            elif blockchain == BlockchainType.SOLANA:
                return GasEstimator.estimate_solana_fee()
            
            elif blockchain == BlockchainType.TON:
                return GasEstimator.estimate_ton_fee(operation)
            
            else:
                logger.warning(f"Fee estimation not supported for {blockchain}")
                return None
        
        except Exception as e:
            logger.error(f"Fee estimation error: {e}")
            return None


class BlockchainHelper:
    """General blockchain helper functions."""

    @staticmethod
    def get_blockchain_decimals(blockchain: BlockchainType) -> int:
        decimals_map = {
            BlockchainType.ETHEREUM: 18,
            BlockchainType.POLYGON: 18,
            BlockchainType.ARBITRUM: 18,
            BlockchainType.OPTIMISM: 18,
            BlockchainType.BASE: 18,
            BlockchainType.AVALANCHE: 18,
            BlockchainType.BITCOIN: 8,
            BlockchainType.SOLANA: 9,
            BlockchainType.TON: 9,
        }
        return decimals_map.get(blockchain, 18)

    @staticmethod
    def get_blockchain_symbol(blockchain: BlockchainType) -> str:
        symbols_map = {
            BlockchainType.ETHEREUM: "ETH",
            BlockchainType.POLYGON: "MATIC",
            BlockchainType.ARBITRUM: "ARB",
            BlockchainType.OPTIMISM: "OP",
            BlockchainType.BASE: "ETH",
            BlockchainType.AVALANCHE: "AVAX",
            BlockchainType.BITCOIN: "BTC",
            BlockchainType.SOLANA: "SOL",
            BlockchainType.TON: "TON",
        }
        return symbols_map.get(blockchain, "UNKNOWN")

    @staticmethod
    def get_blockchain_info(blockchain: BlockchainType) -> Dict[str, any]:
        symbol = BlockchainHelper.get_blockchain_symbol(blockchain)
        decimals = BlockchainHelper.get_blockchain_decimals(blockchain)
        
        return {
            "name": blockchain.value,
            "symbol": symbol,
            "decimals": decimals,
            "type": "layer1" if blockchain in (
                BlockchainType.ETHEREUM, BlockchainType.BITCOIN,
                BlockchainType.SOLANA, BlockchainType.TON, BlockchainType.AVALANCHE
            ) else "layer2",
        }

    @staticmethod
    def format_balance(blockchain: BlockchainType, balance_raw: int) -> str:
        decimals = BlockchainHelper.get_blockchain_decimals(blockchain)
        symbol = BlockchainHelper.get_blockchain_symbol(blockchain)
        
        balance = balance_raw / (10 ** decimals)
        return f"{balance:.6f} {symbol}"

class USDTHelper:
    """Helper class for USDT (Tether) operations across blockchains."""
    
    USDT_DECIMALS = 6  # USDT uses 6 decimals unlike ETH's 18
    
    @staticmethod
    def get_usdt_contract(blockchain: BlockchainType, settings) -> Optional[str]:
        """Get USDT contract address for a specific blockchain."""
        usdt_contracts = {
            BlockchainType.ETHEREUM: settings.usdt_contract_ethereum,
            BlockchainType.POLYGON: settings.usdt_contract_polygon,
            BlockchainType.ARBITRUM: settings.usdt_contract_arbitrum,
            BlockchainType.OPTIMISM: settings.usdt_contract_optimism,
            BlockchainType.AVALANCHE: settings.usdt_contract_avalanche,
            BlockchainType.BASE: settings.usdt_contract_base,
        }
        return usdt_contracts.get(blockchain)
    
    @staticmethod
    def format_usdt(amount_raw: int) -> float:
        """Convert raw USDT amount to decimal format."""
        return amount_raw / (10 ** USDTHelper.USDT_DECIMALS)
    
    @staticmethod
    def parse_usdt(amount: float) -> int:
        """Convert decimal USDT amount to raw format."""
        return int(amount * (10 ** USDTHelper.USDT_DECIMALS))
    
    @staticmethod
    def is_usdt_supported(blockchain: BlockchainType) -> bool:
        """Check if USDT is supported on a blockchain."""
        return blockchain in (
            BlockchainType.ETHEREUM, BlockchainType.POLYGON, BlockchainType.ARBITRUM,
            BlockchainType.OPTIMISM, BlockchainType.AVALANCHE, BlockchainType.BASE
        )
    
    @staticmethod
    def validate_usdt_amount(amount: float, min_transaction: float = 1.0) -> tuple[bool, Optional[str]]:
        """Validate USDT transaction amount."""
        if amount < min_transaction:
            return False, f"Minimum transaction amount is {min_transaction} USDT"
        if amount > 1_000_000:  # Reasonable max
            return False, "Maximum transaction amount is 1,000,000 USDT"
        return True, None