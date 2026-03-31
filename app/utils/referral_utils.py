"""
Referral Code Generation Utility
- Generate unique, pronounceable codes
- Ensure no collisions in database
"""

import logging
import secrets
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User

logger = logging.getLogger(__name__)


async def generate_referral_code(db: AsyncSession, length: int = 10) -> str:
    """
    Generate a unique, cryptographically secure referral code.
    
    Format: REF_XXXXXXXXXX (10 random alphanumeric characters)
    
    Args:
        db: Database session
        length: Length of random suffix
    
    Returns:
        Unique referral code (e.g., "REF_A7K9M2X4")
    """
    characters = string.ascii_uppercase + string.digits
    
    # Try up to 10 times to generate a unique code
    for attempt in range(10):
        random_part = ''.join(secrets.choice(characters) for _ in range(length))
        referral_code = f"REF_{random_part}"
        
        # Check if code already exists
        query = select(User).where(User.referral_code == referral_code)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if not existing:
            logger.debug(f"Generated referral code: {referral_code}")
            return referral_code
    
    # Extremely unlikely to reach here (probability ~1 in 10^30)
    raise RuntimeError("Failed to generate unique referral code after 10 attempts")
