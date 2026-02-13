import pytest
from uuid import uuid4
from decimal import Decimal
from app.services.auth_service import AuthService
from app.services.wallet_service import WalletService
from app.models.wallet import BlockchainType, WalletType
from app.services.nft_service import NFTService
from app.services.marketplace_service import MarketplaceService
from app.models import Escrow, EscrowStatus


@pytest.mark.asyncio
async def test_make_offer_creates_escrow(test_db):
    # create seller
    seller, _ = await AuthService.register_user(db=test_db, email="seller@example.com", username="seller", password="pass123")
    buyer, _ = await AuthService.register_user(db=test_db, email="buyer@example.com", username="buyer", password="pass123")

    # create wallets
    seller_wallet, _ = await WalletService.create_wallet(db=test_db, user_id=seller.id, blockchain=BlockchainType.EVM, wallet_type=WalletType.CUSTODIAL, address="0xseller", is_primary=True)
    buyer_wallet, _ = await WalletService.create_wallet(db=test_db, user_id=buyer.id, blockchain=BlockchainType.EVM, wallet_type=WalletType.CUSTODIAL, address="0xbuyer", is_primary=True)

    # mint NFT
    nft, _ = await NFTService.mint_nft(db=test_db, user_id=seller.id, wallet_id=seller_wallet.id, name="EscrowNFT", description="Test", image_url="https://example.com/image.png", royalty_percentage=5)

    # create listing
    listing, _ = await MarketplaceService.create_listing(db=test_db, nft_id=nft.id, seller_id=seller.id, seller_address=seller_wallet.address, price=Decimal('100.00'), currency="USDT", blockchain="eth")

    # buyer makes offer
    offer, err = await MarketplaceService.make_offer(db=test_db, listing_id=listing.id, buyer_id=buyer.id, buyer_address=buyer_wallet.address, offer_price=Decimal('100.00'), currency="USDT")
    assert err is None
    assert offer is not None

    # check escrow exists
    res = await test_db.execute("SELECT id, amount, commission_amount, status FROM escrows WHERE offer_id = :oid", {"oid": str(offer.id)})
    row = res.fetchone()
    assert row is not None
    assert Decimal(row[1]) == Decimal('100.00')
    # commission should be 2% -> 2.00
    assert Decimal(row[2]) == Decimal('2.00')
    assert row[3] in (EscrowStatus.HELD.value, EscrowStatus.PENDING.value)
