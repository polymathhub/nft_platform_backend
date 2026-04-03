"""
Tests for Phase 2 - Production-grade TON blockchain integration
Tests TonCenter client, background jobs, and error recovery systems
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.toncenter_client import TonCenterClient
from app.services.error_recovery import (
    ErrorRecoveryManager,
    ErrorRecoveryConfig,
    RecoveryStrategy,
    BLOCKCHAIN_QUERY_RECOVERY,
)
from app.jobs.background_verification import (
    TransactionVerificationJob,
    SessionCleanupJob,
)
from app.middleware.session_validator import SessionValidator


@pytest.mark.asyncio
class TestTonCenterClient:
    """Tests for TonCenter API client"""
    
    async def test_client_initialization(self):
        """Test TonCenter client initializes correctly"""
        client = TonCenterClient(api_key="test_key", is_testnet=False)
        assert client.api_key == "test_key"
        assert client.is_testnet == False
        assert client.base_url == TonCenterClient.MAINNET_BASE_URL
        await client.close()
    
    async def test_testnet_client(self):
        """Test testnet configuration"""
        client = TonCenterClient(is_testnet=True)
        assert client.is_testnet == True
        assert client.base_url == TonCenterClient.TESTNET_BASE_URL
        await client.close()
    
    @patch('app.services.toncenter_client.httpx.AsyncClient.request')
    async def test_get_address_balance(self, mock_request):
        """Test balance query"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": "1000000000"}  # 1 TON
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = TonCenterClient()
        result = await client.get_address_balance("UQAom6hkCmec-P7H0xPb8PPpH-p1o6lMPXShB-bHFlDmkK3")
        
        assert result["balance_ton"] == 1.0
        assert result["success"] == True
        await client.close()
    
    @patch('app.services.toncenter_client.httpx.AsyncClient.request')
    async def test_get_transaction_confirmation(self, mock_request):
        """Test transaction confirmation checking"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": {}}
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        client = TonCenterClient()
        result = await client.check_transaction_confirmation("abc123")
        
        assert "tx_hash" in result
        assert "status" in result
        await client.close()


@pytest.mark.asyncio
class TestErrorRecovery:
    """Tests for error recovery system"""
    
    async def test_recovery_manager_init(self):
        """Test recovery manager initialization"""
        manager = ErrorRecoveryManager()
        assert manager is not None
    
    async def test_retry_strategy(self):
        """Test retry recovery strategy"""
        config = ErrorRecoveryConfig(
            strategy=RecoveryStrategy.RETRY,
            max_retries=3,
            initial_delay=0.1,
        )
        
        call_count = 0
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        manager = ErrorRecoveryManager()
        result = await manager.execute_with_recovery(
            "test_op",
            failing_func,
            config
        )
        
        assert result["success"] == True
        assert result["data"] == "success"
        assert result["attempts"] == 3
    
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries exceeded"""
        config = ErrorRecoveryConfig(
            strategy=RecoveryStrategy.RETRY,
            max_retries=2,
            initial_delay=0.1,
            user_message="Operation failed after retries"
        )
        
        async def always_fails():
            raise ValueError("Persistent error")
        
        manager = ErrorRecoveryManager()
        result = await manager.execute_with_recovery(
            "test_op",
            always_fails,
            config
        )
        
        assert result["success"] == False
        assert result["attempts"] <= 3
        assert result["user_message"] == "Operation failed after retries"
    
    async def test_fallback_strategy(self):
        """Test fallback recovery strategy"""
        config = ErrorRecoveryConfig(
            strategy=RecoveryStrategy.FALLBACK,
            fallback_value={"cached": True},
            user_message="Using cached data"
        )
        
        async def failing_func():
            raise ValueError("API error")
        
        manager = ErrorRecoveryManager()
        result = await manager.execute_with_recovery(
            "test_op",
            failing_func,
            config
        )
        
        assert result["success"] == True
        assert result["data"] == {"cached": True}
        assert "fallback" in result["strategy"]


@pytest.mark.asyncio
class TestBackgroundJobs:
    """Tests for background verification job"""
    
    def test_job_initialization(self):
        """Test job initializes correctly"""
        job = TransactionVerificationJob()
        assert job.is_running == False
        assert job.verifier is not None
    
    async def test_calculate_next_verification(self):
        """Test verification scheduling calculation"""
        from app.models.blockchain_transaction import BlockchainTransactionStatus
        
        job = TransactionVerificationJob()
        
        # Test pending status
        next_time = job._calculate_next_verification(BlockchainTransactionStatus.PENDING)
        assert next_time > datetime.utcnow()
        
        # Test confirmed status (no further verification needed)
        next_time = job._calculate_next_verification(BlockchainTransactionStatus.CONFIRMED)
        assert (next_time - datetime.utcnow()).days >= 364
    
    def test_session_cleanup_job_init(self):
        """Test session cleanup job"""
        job = SessionCleanupJob()
        assert job.is_running == False


@pytest.mark.asyncio
class TestSessionValidator:
    """Tests for session validation"""
    
    def test_validator_initialization(self):
        """Test session validator initializes"""
        validator = SessionValidator()
        assert validator is not None
    
    async def test_create_session_hash(self):
        """Test session hash generation"""
        validator = SessionValidator()
        hash1 = await validator.create_session_hash(
            "user123",
            "UQAom6hkCmec",
            {"platform": "web", "name": "chrome"}
        )
        
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest length
    
    async def test_create_different_hashes_for_different_devices(self):
        """Test different device fingerprints create different hashes"""
        validator = SessionValidator()
        
        hash1 = await validator.create_session_hash(
            "user123",
            "UQAom6hkCmec",
            {"platform": "web", "name": "chrome"}
        )
        
        hash2 = await validator.create_session_hash(
            "user123",
            "UQAom6hkCmec",
            {"platform": "ios", "name": "safari"}
        )
        
        assert hash1 != hash2


def test_recovery_delay_calculation():
    """Test exponential backoff delay calculation"""
    config = ErrorRecoveryConfig(
        initial_delay=1.0,
        max_delay=60.0,
        backoff_multiplier=2.0
    )
    
    from app.services.error_recovery import RecoveryContext
    ctx = RecoveryContext("test", config)
    
    # Simulate multiple failures
    for i in range(1, 6):
        ctx.attempt = i
        delay = ctx.get_next_delay()
        expected = min(1.0 * (2.0 ** (i - 1)), 60.0)
        assert abs(delay - expected) < 0.1


def test_blockchain_query_recovery_config():
    """Test blockchain query recovery configuration"""
    assert BLOCKCHAIN_QUERY_RECOVERY.strategy == RecoveryStrategy.RETRY
    assert BLOCKCHAIN_QUERY_RECOVERY.max_retries == 5
    assert BLOCKCHAIN_QUERY_RECOVERY.initial_delay == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
