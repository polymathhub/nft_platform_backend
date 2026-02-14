import pytest
from uuid import uuid4
from app.services.notification_service import (
    NotificationService,
    Notification,
    NotificationType,
)


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def send_json(self, data):
        """Store sent message."""
        self.messages.append(data)


@pytest.mark.asyncio
async def test_notification_creation():
    """Test notification creation."""
    user_id = uuid4()
    notification = Notification(
        notification_type=NotificationType.NFT_MINTED,
        user_id=user_id,
        title="NFT Minted",
        message="Your NFT has been minted",
        data={"nft_name": "Test NFT"},
    )
    
    assert notification.type == NotificationType.NFT_MINTED
    assert notification.user_id == user_id
    assert notification.title == "NFT Minted"
    assert notification.read is False


def test_notification_to_dict():
    """Test notification to dictionary conversion."""
    user_id = uuid4()
    notification = Notification(
        notification_type=NotificationType.NFT_MINTED,
        user_id=user_id,
        title="NFT Minted",
        message="Your NFT has been minted",
    )
    
    data = notification.to_dict()
    assert data["type"] == "nft_minted"
    assert data["user_id"] == str(user_id)
    assert data["title"] == "NFT Minted"


def test_notification_to_json():
    """Test notification to JSON conversion."""
    user_id = uuid4()
    notification = Notification(
        notification_type=NotificationType.NFT_MINTED,
        user_id=user_id,
        title="NFT Minted",
        message="Your NFT has been minted",
    )
    
    json_str = notification.to_json()
    assert isinstance(json_str, str)
    assert "nft_minted" in json_str
    assert str(user_id) in json_str


@pytest.mark.asyncio
async def test_notification_service_connect():
    """Test WebSocket connection."""
    user_id = uuid4()
    ws = MockWebSocket()
    
    await NotificationService.connect(user_id, ws)
    
    assert user_id in NotificationService.active_connections
    assert ws in NotificationService.active_connections[user_id]


@pytest.mark.asyncio
async def test_notification_service_disconnect():
    """Test WebSocket disconnection."""
    user_id = uuid4()
    ws = MockWebSocket()
    
    await NotificationService.connect(user_id, ws)
    await NotificationService.disconnect(user_id, ws)
    
    assert user_id not in NotificationService.active_connections


@pytest.mark.asyncio
async def test_send_notification():
    """Test sending notification."""
    user_id = uuid4()
    ws = MockWebSocket()
    
    await NotificationService.connect(user_id, ws)
    
    notification = Notification(
        notification_type=NotificationType.NFT_MINTED,
        user_id=user_id,
        title="Test",
        message="Test message",
    )
    
    await NotificationService.send_notification(user_id, notification)
    
    assert len(ws.messages) == 1
    assert ws.messages[0]["type"] == "nft_minted"


@pytest.mark.asyncio
async def test_notify_nft_minted():
    """Test NFT minted notification."""
    user_id = uuid4()
    ws = MockWebSocket()
    
    await NotificationService.connect(user_id, ws)
    
    await NotificationService.notify_nft_minted(
        user_id=user_id,
        nft_name="Test NFT",
        nft_id=str(uuid4()),
        contract_address="0Qxxx",
        token_id="1",
    )
    
    assert len(ws.messages) == 1
    assert ws.messages[0]["type"] == "nft_minted"
    assert "Test NFT" in ws.messages[0]["message"]


@pytest.mark.asyncio
async def test_notify_transaction_confirmed():
    """Test transaction confirmed notification."""
    user_id = uuid4()
    ws = MockWebSocket()
    
    await NotificationService.connect(user_id, ws)
    
    await NotificationService.notify_transaction_confirmed(
        user_id=user_id,
        tx_hash="0x1234567890",
        action="mint",
    )
    
    assert len(ws.messages) == 1
    assert ws.messages[0]["type"] == "transaction_confirmed"


@pytest.mark.asyncio
async def test_get_active_users():
    """Test getting active user count."""
    NotificationService.active_connections.clear()
    
    user_id1 = uuid4()
    user_id2 = uuid4()
    
    await NotificationService.connect(user_id1, MockWebSocket())
    await NotificationService.connect(user_id2, MockWebSocket())
    
    active = NotificationService.get_active_users()
    assert active == 2
