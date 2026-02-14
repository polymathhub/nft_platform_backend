import pytest
from uuid import uuid4
from app.models import User, Wallet
from app.models.wallet import BlockchainType, WalletType
from app.services.wallet_service import WalletService
from app.services.auth_service import AuthService


@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    user, _ = await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="testuser",
        password="securepass123",
    )
    return user


@pytest.mark.asyncio
async def test_create_wallet(test_db, test_user):
    """Test wallet creation."""
    wallet, error = await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.TON,
        wallet_type=WalletType.CUSTODIAL,
        address="0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1zQU",
        is_primary=True,
    )
    
    assert error is None
    assert wallet is not None
    assert wallet.address == "0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1zQU"
    assert wallet.blockchain == BlockchainType.TON
    assert wallet.is_primary is True


@pytest.mark.asyncio
async def test_create_duplicate_wallet(test_db, test_user):
    """Test creating wallet with duplicate address."""
    address = "0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1zQU"
    
    # Create first wallet
    await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.TON,
        wallet_type=WalletType.CUSTODIAL,
        address=address,
    )
    
    # Try to create wallet with same address
    wallet, error = await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.SOLANA,
        wallet_type=WalletType.CUSTODIAL,
        address=address,
    )
    
    assert wallet is None
    assert error is not None


@pytest.mark.asyncio
async def test_get_user_wallets(test_db, test_user):
    """Test getting user wallets."""
    # Create two wallets
    await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.TON,
        wallet_type=WalletType.CUSTODIAL,
        address="address1",
    )
    
    await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.SOLANA,
        wallet_type=WalletType.CUSTODIAL,
        address="address2",
    )
    
    wallets = await WalletService.get_user_wallets(test_db, test_user.id)
    assert len(wallets) == 2


@pytest.mark.asyncio
async def test_get_primary_wallet(test_db, test_user):
    """Test getting primary wallet."""
    await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.TON,
        wallet_type=WalletType.CUSTODIAL,
        address="address1",
        is_primary=True,
    )
    
    primary = await WalletService.get_primary_wallet(
        test_db, test_user.id, BlockchainType.TON
    )
    
    assert primary is not None
    assert primary.is_primary is True
    assert primary.blockchain == BlockchainType.TON
