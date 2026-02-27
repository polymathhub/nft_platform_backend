"""
Professional Design System Constants
Aligns backend with modern frontend design patterns
"""

from enum import Enum
from typing import NamedTuple

# ============================================================================
# PRIMARY BRAND COLORS - GiftedForge Color Palette
# Based on modern fintech/enterprise applications
# ============================================================================

class PrimaryColors:
    """Primary brand colors matching frontend design."""
    # Vibrant purple gradient (hero/CTA)
    PURPLE_LIGHT = "#7C59FF"
    PURPLE_DARK = "#5B3FBF"
    PURPLE_PRIMARY = "#6B4FFF"
    
    # Supporting colors
    WHITE = "#FFFFFF"
    DARK_BG = "#0F0F1E"
    DARK_SECONDARY = "#1A1A2E"
    
    # Status colors
    SUCCESS = "#4CAF50"
    WARNING = "#FFC107"
    ERROR = "#F44336"
    INFO = "#2196F3"


class SecondaryColors:
    """Secondary/accent colors for UI elements."""
    BLUE_ACCENT = "#2196F3"
    GREEN_ACCENT = "#4CAF50"
    ORANGE_ACCENT = "#FF9800"
    RED_ACCENT = "#F44336"
    GRAY_LIGHT = "#F5F5F5"
    GRAY_MEDIUM = "#999999"
    GRAY_DARK = "#333333"


class GradientColors:
    """Gradient definitions for visual hierarchy."""
    PURPLE_GRADIENT = f"linear-gradient(135deg, {PrimaryColors.PURPLE_LIGHT} 0%, {PrimaryColors.PURPLE_DARK} 100%)"
    ACCENT_GRADIENT = f"linear-gradient(135deg, {SecondaryColors.BLUE_ACCENT} 0%, {PrimaryColors.PURPLE_PRIMARY} 100%)"
    NEUTRAL_GRADIENT = f"linear-gradient(135deg, {SecondaryColors.GRAY_LIGHT} 0%, {SecondaryColors.GRAY_MEDIUM} 100%)"


# ============================================================================
# TEXT STYLING GUIDES
# ============================================================================

class Typography:
    """Typography specifications for professional appearance."""
    
    # Heading sizes
    HEADING_1_SIZE = "32px"
    HEADING_2_SIZE = "24px"
    HEADING_3_SIZE = "20px"
    HEADING_4_SIZE = "18px"
    BODY_SIZE = "16px"
    SMALL_SIZE = "14px"
    CAPTION_SIZE = "12px"
    
    # Font weights
    BOLD = 700
    SEMIBOLD = 600
    MEDIUM = 500
    REGULAR = 400
    LIGHT = 300
    
    # Line heights
    TIGHT = 1.2
    NORMAL = 1.5
    LOOSE = 1.8


# ============================================================================
# STATUS INDICATORS
# ============================================================================

class StatusIndicators(Enum):
    """Professional status indicators without emojis."""
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    SUCCESS = "Success"
    FAILED = "Failed"
    ERROR = "Error"
    WARNING = "Warning"
    INFO = "Information"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    LOCKED = "Locked"
    UNLOCKED = "Unlocked"
    MINTING = "Minting"
    MINTED = "Minted"
    TRANSFERRED = "Transferred"
    BURNED = "Burned"


class StatusColors:
    """Color mapping for status indicators."""
    COLORS = {
        StatusIndicators.PENDING: SecondaryColors.ORANGE_ACCENT,
        StatusIndicators.PROCESSING: SecondaryColors.BLUE_ACCENT,
        StatusIndicators.COMPLETED: SecondaryColors.GREEN_ACCENT,
        StatusIndicators.SUCCESS: SecondaryColors.GREEN_ACCENT,
        StatusIndicators.FAILED: SecondaryColors.RED_ACCENT,
        StatusIndicators.ERROR: SecondaryColors.RED_ACCENT,
        StatusIndicators.WARNING: SecondaryColors.ORANGE_ACCENT,
        StatusIndicators.INFO: SecondaryColors.BLUE_ACCENT,
        StatusIndicators.ACTIVE: SecondaryColors.GREEN_ACCENT,
        StatusIndicators.INACTIVE: SecondaryColors.GRAY_MEDIUM,
        StatusIndicators.LOCKED: SecondaryColors.RED_ACCENT,
        StatusIndicators.UNLOCKED: SecondaryColors.GREEN_ACCENT,
        StatusIndicators.MINTING: SecondaryColors.BLUE_ACCENT,
        StatusIndicators.MINTED: SecondaryColors.GREEN_ACCENT,
        StatusIndicators.TRANSFERRED: SecondaryColors.BLUE_ACCENT,
        StatusIndicators.BURNED: SecondaryColors.RED_ACCENT,
    }

    @classmethod
    def get_color(cls, status: StatusIndicators) -> str:
        """Get color for a specific status."""
        return cls.COLORS.get(status, SecondaryColors.GRAY_MEDIUM)

    @classmethod
    def get_status_display(cls, status: str) -> str:
        """Convert status string to display text with color info."""
        try:
            indicator = StatusIndicators(status)
            color = cls.get_color(indicator)
            return f"{indicator.value}"
        except ValueError:
            return status


# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================

class MessageTemplates:
    """Professional message templates for API responses and notifications."""
    
    # Success messages
    SUCCESS_CREATED = "{resource} created successfully"
    SUCCESS_UPDATED = "{resource} updated successfully"
    SUCCESS_DELETED = "{resource} deleted successfully"
    SUCCESS_PROCESSED = "{action} completed successfully"
    
    # Error messages
    ERROR_NOT_FOUND = "{resource} not found"
    ERROR_INVALID_INPUT = "Invalid input provided"
    ERROR_UNAUTHORIZED = "Unauthorized access"
    ERROR_FORBIDDEN = "Access forbidden"
    ERROR_SERVER_ERROR = "An error occurred while processing your request"
    ERROR_VALIDATION = "Validation failed: {details}"
    ERROR_CONFLICT = "Resource conflict: {details}"
    
    # Notification messages
    NOTIFY_MINTING_STARTED = "NFT minting has started"
    NOTIFY_MINTING_COMPLETE = "NFT has been minted successfully"
    NOTIFY_LISTING_CREATED = "NFT has been listed for sale"
    NOTIFY_OFFER_RECEIVED = "You have received an offer"
    NOTIFY_TRANSACTION_CONFIRMED = "Transaction confirmed"
    NOTIFY_WALLET_CREATED = "Wallet created successfully"
    
    @classmethod
    def format_success(cls, action: str, resource: str) -> str:
        """Format a success message."""
        return f"{resource} {action} successfully"
    
    @classmethod
    def format_error(cls, error_type: str, details: str = "") -> str:
        """Format an error message."""
        messages = {
            "not_found": f" not found",
            "invalid": f"Invalid input",
            "unauthorized": f"Unauthorized access",
            "server_error": f"Server error occurred",
        }
        base = messages.get(error_type, "An error occurred")
        return f"{base}: {details}" if details else base


# ============================================================================
# SPACING & LAYOUT
# ============================================================================

class Spacing:
    """Standardized spacing system."""
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"


class BorderRadius:
    """Standardized border radius values."""
    NONE = "0px"
    SM = "4px"
    MD = "8px"
    LG = "12px"
    FULL = "9999px"


class Elevation:
    """Shadow/elevation system."""
    NONE = "0 0 0 0 rgba(0,0,0,0)"
    SM = "0 1px 2px 0 rgba(0,0,0,0.05)"
    MD = "0 4px 6px -1px rgba(0,0,0,0.1)"
    LG = "0 10px 15px -3px rgba(0,0,0,0.1)"
    XL = "0 20px 25px -5px rgba(0,0,0,0.1)"
    XXL = "0 25px 50px -12px rgba(0,0,0,0.25)"


# ============================================================================
# API RESPONSE FORMATTING
# ============================================================================

class ResponseFormat(NamedTuple):
    """Standard response format for all API endpoints."""
    success: bool
    status_code: int
    title: str
    message: str
    data: dict = None
    timestamp: str = None


class HTTPStatusCodes:
    """Standard HTTP status codes with professional messages."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE = 422
    RATE_LIMITED = 429
    SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    
    MESSAGES = {
        200: "OK",
        201: "Created",
        202: "Accepted",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Rate Limited",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }

    @classmethod
    def get_message(cls, code: int) -> str:
        """Get standard message for HTTP status code."""
        return cls.MESSAGES.get(code, "Unknown Status")


# ============================================================================
# PROFESSIONAL LOGGING FORMAT
# ============================================================================

LOG_FORMAT_STANDARD = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
LOG_FORMAT_DETAILED = "[%(asctime)s] %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_FORMAT_JSON = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
