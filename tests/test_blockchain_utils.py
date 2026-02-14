import pytest
from app.models.wallet import BlockchainType
from app.utils.blockchain_utils import (
    AddressValidator,
    UnitConverter,
    GasEstimator,
    BlockchainHelper,
)


class TestAddressValidator:
    """Test address validation."""

    def test_ethereum_address_valid(self):
        """Test valid Ethereum address."""
        # Valid Ethereum address
        valid_addr = "0x742d35Cc6634C0532925a3b844Bc9e7595f42bE"
        is_valid, error = AddressValidator.validate_ethereum_address(valid_addr)
        assert is_valid is True
        assert error is None

    def test_ethereum_address_valid_without_prefix(self):
        """Test valid Ethereum address without 0x prefix."""
        valid_addr = "742d35Cc6634C0532925a3b844Bc9e7595f42bE"
        is_valid, error = AddressValidator.validate_ethereum_address(valid_addr)
        assert is_valid is True
        assert error is None

    def test_ethereum_address_invalid_length(self):
        """Test invalid Ethereum address length."""
        invalid_addr = "0x742d35Cc6634C0532925a3b844Bc9e7595f42"
        is_valid, error = AddressValidator.validate_ethereum_address(invalid_addr)
        assert is_valid is False
        assert error is not None

    def test_bitcoin_address_p2pkh(self):
        """Test valid Bitcoin P2PKH address."""
        valid_addr = "1A1z7agoat2QJVNT3WQHAZH7uS5Z1cKur5"
        is_valid, error = AddressValidator.validate_bitcoin_address(valid_addr)
        assert is_valid is True

    def test_bitcoin_address_p2sh(self):
        """Test valid Bitcoin P2SH address."""
        valid_addr = "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy"
        is_valid, error = AddressValidator.validate_bitcoin_address(valid_addr)
        assert is_valid is True

    def test_bitcoin_address_segwit(self):
        """Test valid Bitcoin Segwit address."""
        valid_addr = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        is_valid, error = AddressValidator.validate_bitcoin_address(valid_addr)
        assert is_valid is True

    def test_solana_address_valid(self):
        """Test valid Solana address."""
        valid_addr = "TokenkegQfeZyiNwAJsyFbPVwwQQyAH9FSVqNTCcboQ"
        is_valid, error = AddressValidator.validate_solana_address(valid_addr)
        assert is_valid is True

    def test_ton_address_valid(self):
        """Test valid TON address."""
        valid_addr = "0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1zQU"
        is_valid, error = AddressValidator.validate_ton_address(valid_addr)
        assert is_valid is True

    def test_validate_address_ethereum(self):
        """Test validate_address for Ethereum."""
        valid_addr = "0x742d35Cc6634C0532925a3b844Bc9e7595f42bE"
        is_valid, error = AddressValidator.validate_address(BlockchainType.ETHEREUM, valid_addr)
        assert is_valid is True

    def test_validate_address_bitcoin(self):
        """Test validate_address for Bitcoin."""
        valid_addr = "1A1z7agoat2QJVNT3WQHAZH7uS5Z1cKur5"
        is_valid, error = AddressValidator.validate_address(BlockchainType.BITCOIN, valid_addr)
        assert is_valid is True


class TestUnitConverter:
    """Test unit conversions."""

    def test_wei_to_eth(self):
        """Test wei to ETH conversion."""
        # 1 ETH = 10^18 wei
        wei = 10**18
        eth = UnitConverter.wei_to_eth(wei)
        assert eth == 1.0

    def test_eth_to_wei(self):
        """Test ETH to wei conversion."""
        eth = 1.0
        wei = UnitConverter.eth_to_wei(eth)
        assert wei == 10**18

    def test_gwei_to_eth(self):
        """Test GWEI to ETH conversion."""
        # 1 ETH = 10^9 GWEI
        gwei = 10**9
        eth = UnitConverter.gwei_to_eth(gwei)
        assert eth == 1.0

    def test_gwei_to_wei(self):
        """Test GWEI to wei conversion."""
        # 1 GWEI = 10^9 wei
        gwei = 1.0
        wei = UnitConverter.gwei_to_wei(gwei)
        assert wei == 10**9

    def test_satoshi_to_btc(self):
        """Test satoshi to BTC conversion."""
        # 1 BTC = 10^8 satoshis
        satoshi = 10**8
        btc = UnitConverter.satoshi_to_btc(satoshi)
        assert btc == 1.0

    def test_btc_to_satoshi(self):
        """Test BTC to satoshi conversion."""
        btc = 1.0
        satoshi = UnitConverter.btc_to_satoshi(btc)
        assert satoshi == 10**8

    def test_lamport_to_sol(self):
        """Test lamport to SOL conversion."""
        # 1 SOL = 10^9 lamports
        lamports = 10**9
        sol = UnitConverter.lamport_to_sol(lamports)
        assert sol == 1.0

    def test_convert_units_ethereum(self):
        """Test convert_units for Ethereum."""
        # 1 ETH to wei
        result = UnitConverter.convert_units(BlockchainType.ETHEREUM, 1.0, "eth", "wei")
        assert result == float(10**18)

    def test_convert_units_bitcoin(self):
        """Test convert_units for Bitcoin."""
        # 1 BTC to satoshi
        result = UnitConverter.convert_units(BlockchainType.BITCOIN, 1.0, "btc", "satoshi")
        assert result == float(10**8)

    def test_convert_units_solana(self):
        """Test convert_units for Solana."""
        # 1 SOL to lamport
        result = UnitConverter.convert_units(BlockchainType.SOLANA, 1.0, "sol", "lamport")
        assert result == float(10**9)


class TestGasEstimator:
    """Test gas/fee estimation."""

    def test_estimate_ethereum_gas_cost(self):
        """Test Ethereum gas cost estimation."""
        # Transfer operation: 21000 gas at 20 gwei
        # Cost: 21000 * 20 = 420000 gwei = 0.00042 ETH
        cost = GasEstimator.estimate_ethereum_gas_cost("transfer", 20.0)
        assert cost is not None
        assert 0.0004 < cost < 0.0005

    def test_estimate_ethereum_nft_mint(self):
        """Test Ethereum NFT mint cost estimation."""
        # Mint operation: 100000 gas at 25 gwei
        cost = GasEstimator.estimate_ethereum_gas_cost("nft_mint", 25.0)
        assert cost is not None
        assert cost > 0

    def test_estimate_bitcoin_fee_normal(self):
        """Test Bitcoin fee estimation (normal rate)."""
        # 250 bytes at 30 sat/byte = 7500 satoshis
        fee = GasEstimator.estimate_bitcoin_fee(250, "normal")
        assert fee is not None
        assert UnitConverter.btc_to_satoshi(fee) == 7500

    def test_estimate_bitcoin_fee_fast(self):
        """Test Bitcoin fee estimation (fast rate)."""
        fee_fast = GasEstimator.estimate_bitcoin_fee(250, "fast")
        fee_normal = GasEstimator.estimate_bitcoin_fee(250, "normal")
        assert fee_fast > fee_normal

    def test_estimate_solana_fee(self):
        """Test Solana fee estimation."""
        fee = GasEstimator.estimate_solana_fee()
        assert fee > 0
        # Should be around 0.000005 SOL (5000 lamports)
        assert fee < 0.00001

    def test_estimate_ton_fee(self):
        """Test TON fee estimation."""
        fee_message = GasEstimator.estimate_ton_fee("message")
        fee_contract = GasEstimator.estimate_ton_fee("contract")
        assert fee_message < fee_contract

    def test_estimate_fee_ethereum(self):
        """Test estimate_fee for Ethereum."""
        fee = GasEstimator.estimate_fee(BlockchainType.ETHEREUM, "transfer", gas_price_gwei=20.0)
        assert fee is not None
        assert fee > 0

    def test_estimate_fee_bitcoin(self):
        """Test estimate_fee for Bitcoin."""
        fee = GasEstimator.estimate_fee(BlockchainType.BITCOIN, "transfer", tx_size_bytes=250)
        assert fee is not None
        assert fee > 0


class TestBlockchainHelper:
    """Test blockchain helper functions."""

    def test_get_blockchain_decimals(self):
        """Test blockchain decimals retrieval."""
        assert BlockchainHelper.get_blockchain_decimals(BlockchainType.ETHEREUM) == 18
        assert BlockchainHelper.get_blockchain_decimals(BlockchainType.BITCOIN) == 8
        assert BlockchainHelper.get_blockchain_decimals(BlockchainType.SOLANA) == 9

    def test_get_blockchain_symbol(self):
        """Test blockchain symbol retrieval."""
        assert BlockchainHelper.get_blockchain_symbol(BlockchainType.ETHEREUM) == "ETH"
        assert BlockchainHelper.get_blockchain_symbol(BlockchainType.BITCOIN) == "BTC"
        assert BlockchainHelper.get_blockchain_symbol(BlockchainType.POLYGON) == "MATIC"
        assert BlockchainHelper.get_blockchain_symbol(BlockchainType.ARBITRUM) == "ARB"

    def test_get_blockchain_info(self):
        """Test blockchain info retrieval."""
        info = BlockchainHelper.get_blockchain_info(BlockchainType.ETHEREUM)
        assert info["name"] == "ethereum"
        assert info["symbol"] == "ETH"
        assert info["decimals"] == 18
        assert info["type"] == "layer1"

    def test_get_blockchain_info_polygon(self):
        """Test blockchain info for Layer 2."""
        info = BlockchainHelper.get_blockchain_info(BlockchainType.POLYGON)
        assert info["name"] == "polygon"
        assert info["symbol"] == "MATIC"
        assert info["type"] == "layer2"

    def test_format_balance_ethereum(self):
        """Test balance formatting for Ethereum."""
        # 1.5 ETH = 1.5 * 10^18 wei
        balance_wei = int(1.5 * (10**18))
        formatted = BlockchainHelper.format_balance(BlockchainType.ETHEREUM, balance_wei)
        assert "1.500000 ETH" in formatted

    def test_format_balance_bitcoin(self):
        """Test balance formatting for Bitcoin."""
        # 0.5 BTC = 0.5 * 10^8 satoshi
        balance_satoshi = int(0.5 * (10**8))
        formatted = BlockchainHelper.format_balance(BlockchainType.BITCOIN, balance_satoshi)
        assert "0.500000 BTC" in formatted

