import pytest
from uuid import uuid4
from app.models import User, Wallet, NFT
from app.models.wallet import BlockchainType, WalletType
from app.models.nft import NFTStatus
from app.services.nft_service import NFTService
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


@pytest.fixture
async def test_wallet(test_db, test_user):
    """Create a test wallet."""
    wallet, _ = await WalletService.create_wallet(
        db=test_db,
        user_id=test_user.id,
        blockchain=BlockchainType.TON,
        wallet_type=WalletType.CUSTODIAL,
        address="0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1zQU",
        is_primary=True,
    )
    return wallet


@pytest.mark.asyncio
async def test_mint_nft(test_db, test_user, test_wallet):
    """Test NFT minting."""
    nft, error = await NFTService.mint_nft(
        db=test_db,
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        name="My First NFT",
        description="A test NFT",
        image_url="https://example.com/image.png",
        royalty_percentage=10,
        metadata={"rarity": "rare"},
    )
    
    assert error is None
    assert nft is not None
    assert nft.name == "My First NFT"
    assert nft.status == NFTStatus.PENDING
    assert nft.royalty_percentage == 10


@pytest.mark.asyncio
async def test_mint_nft_invalid_wallet(test_db, test_user):
    """Test minting with invalid wallet."""
    nft, error = await NFTService.mint_nft(
        db=test_db,
        user_id=test_user.id,
        wallet_id=uuid4(),
        name="My NFT",
        description="Test",
        image_url="https://example.com/image.png",
        royalty_percentage=5,
    )
    
    assert nft is None
    assert error is not None


@pytest.mark.asyncio
async def test_update_nft_after_mint(test_db, test_user, test_wallet):
    """Test updating NFT after mint."""
    # Create NFT
    nft, _ = await NFTService.mint_nft(
        db=test_db,
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        name="My NFT",
        description="Test",
        image_url="https://example.com/image.png",
        royalty_percentage=5,
    )
    
    # Update after mint
    updated_nft, error = await NFTService.update_nft_after_mint(
        db=test_db,
        nft_id=nft.id,
        contract_address="0QD0xFTB41RYUU4pLd1G5bSr3j79OnyoZVcRJX4wvZPH1234",
        token_id="1",
        transaction_hash="0x1234567890abcdef",
        ipfs_hash="QmXxxx",
    )
    
    assert error is None
    assert updated_nft is not None
    assert updated_nft.status == NFTStatus.MINTED
    assert updated_nft.contract_address is not None
    assert updated_nft.token_id == "1"


@pytest.mark.asyncio
async def test_get_user_nfts(test_db, test_user, test_wallet):
    """Test getting user NFTs."""
    # Create multiple NFTs
    for i in range(3):
        await NFTService.mint_nft(
            db=test_db,
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            name=f"NFT {i+1}",
            description="Test",
            image_url="https://example.com/image.png",
            royalty_percentage=5,
        )
    
    nfts, total = await NFTService.get_user_nfts(test_db, test_user.id)
    assert len(nfts) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_transfer_nft(test_db, test_user, test_wallet):
    """Test NFT transfer."""
    # Create and mint NFT
    nft, _ = await NFTService.mint_nft(
        db=test_db,
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        name="My NFT",
        description="Test",
        image_url="https://example.com/image.png",
        royalty_percentage=5,
    )
    
    # Update to minted status
    await NFTService.update_nft_after_mint(
        db=test_db,
        nft_id=nft.id,
        contract_address="0Qxxx",
        token_id="1",
        transaction_hash="0x1234",
    )
    
    # Transfer NFT
    new_address = "0QNewAddress123"
    transferred_nft, error = await NFTService.transfer_nft(
        db=test_db,
        nft_id=nft.id,
        to_address=new_address,
        transaction_hash="0x5678",
    )
    
    assert error is None
    assert transferred_nft is not None
    assert transferred_nft.owner_address == new_address
    assert transferred_nft.status == NFTStatus.TRANSFERRED
