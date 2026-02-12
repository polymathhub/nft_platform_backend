import pytest
from app.routers.telegram_mint_router import (
    TelegramUser,
    TelegramMessage,
    TelegramUpdate,
)


class TestTelegramRouter:
    """Test Telegram Router functionality"""

    @pytest.fixture
    def telegram_user(self):
        """Create test Telegram user"""
        return TelegramUser(
            id=123456789,
            is_bot=False,
            first_name="Test",
            last_name="User",
            username="testuser",
        )

    @pytest.fixture
    def telegram_message(self, telegram_user):
        """Create test Telegram message"""
        return TelegramMessage(
            message_id=1,
            date=1234567890,
            chat={"id": 123456789},
            **{"from": telegram_user.dict()},
            text="/start",
        )

    def test_telegram_user_model(self, telegram_user):
        """Test TelegramUser model"""
        assert telegram_user.id == 123456789
        assert telegram_user.first_name == "Test"
        assert telegram_user.username == "testuser"

    def test_telegram_message_model(self, telegram_message):
        """Test TelegramMessage model"""
        assert telegram_message.message_id == 1
        assert telegram_message.text == "/start"
        assert telegram_message.chat["id"] == 123456789

    def test_telegram_update_model(self, telegram_message):
        """Test TelegramUpdate model"""
        update = TelegramUpdate(
            update_id=1,
            message=telegram_message,
        )
        assert update.update_id == 1
        assert update.message.text == "/start"


# Command integration tests
class TestCommandParsing:
    """Test command parsing and execution"""

    def test_mint_command_parsing(self):
        """Test /mint command parsing"""
        command = "/mint 550e8400-e29b-41d4-a716-446655440000 MyNFT 'Description'"
        parts = command.split(maxsplit=3)

        assert parts[0] == "/mint"
        assert parts[1] == "550e8400-e29b-41d4-a716-446655440000"
        assert parts[2] == "MyNFT"

    def test_list_command_parsing(self):
        """Test /list command parsing"""
        command = "/list 550e8400-e29b-41d4-a716-446655440002 99.99 USDT"
        parts = command.split()

        assert parts[0] == "/list"
        assert parts[1] == "550e8400-e29b-41d4-a716-446655440002"
        assert parts[2] == "99.99"
        assert parts[3] == "USDT"

    def test_offer_command_parsing(self):
        """Test /offer command parsing"""
        command = "/offer abc12345-def6-4890 45.50"
        parts = command.split()

        assert parts[0] == "/offer"
        assert parts[1] == "abc12345-def6-4890"
        assert parts[2] == "45.50"

    def test_transfer_command_parsing(self):
        """Test /transfer command parsing"""
        command = "/transfer 550e8400-e29b-41d4 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        parts = command.split(maxsplit=2)

        assert parts[0] == "/transfer"
        assert parts[1] == "550e8400-e29b-41d4"
        assert "0x" in parts[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
