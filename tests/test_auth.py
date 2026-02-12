import pytest
from uuid import uuid4
from app.models import User
from app.services.auth_service import AuthService
from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_register_user(test_db):
    """Test user registration."""
    user, error = await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="testuser",
        password="securepass123",
        full_name="Test User",
    )
    
    assert error is None
    assert user is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"


@pytest.mark.asyncio
async def test_register_duplicate_email(test_db):
    """Test registering with duplicate email."""
    # Register first user
    await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="testuser",
        password="securepass123",
    )
    
    # Try to register with same email
    user, error = await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="anotheruser",
        password="securepass123",
    )
    
    assert user is None
    assert error is not None
    assert "already" in error.lower()


@pytest.mark.asyncio
async def test_authenticate_user(test_db):
    """Test user authentication."""
    # Register user
    await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="testuser",
        password="securepass123",
    )
    
    # Authenticate
    user, error = await AuthService.authenticate_user(
        db=test_db,
        email="test@example.com",
        password="securepass123",
    )
    
    assert error is None
    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_authenticate_invalid_password(test_db):
    """Test authentication with invalid password."""
    # Register user
    await AuthService.register_user(
        db=test_db,
        email="test@example.com",
        username="testuser",
        password="securepass123",
    )
    
    # Try with wrong password
    user, error = await AuthService.authenticate_user(
        db=test_db,
        email="test@example.com",
        password="wrongpassword",
    )
    
    assert user is None
    assert error is not None


def test_generate_tokens():
    """Test token generation."""
    user_id = uuid4()
    tokens = AuthService.generate_tokens(user_id)
    
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "expires_in" in tokens
    assert tokens["access_token"] is not None
    assert tokens["refresh_token"] is not None


def test_verify_token():
    """Test token verification."""
    user_id = uuid4()
    tokens = AuthService.generate_tokens(user_id)
    
    verified_id = AuthService.verify_token(tokens["access_token"])
    assert verified_id == user_id


def test_verify_invalid_token():
    """Test verification of invalid token."""
    verified_id = AuthService.verify_token("invalid.token.here")
    assert verified_id is None
