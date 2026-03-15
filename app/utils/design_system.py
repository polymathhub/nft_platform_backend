from enum import Enum
from typing import NamedTuple
class PrimaryColors:
    PURPLE_LIGHT = "
    PURPLE_DARK = "
    PURPLE_PRIMARY = "
    WHITE = "
    DARK_BG = "
    DARK_SECONDARY = "
    SUCCESS = "
    WARNING = "
    ERROR = "
    INFO = "
class SecondaryColors:
    BLUE_ACCENT = "
    GREEN_ACCENT = "
    ORANGE_ACCENT = "
    RED_ACCENT = "
    GRAY_LIGHT = "
    GRAY_MEDIUM = "
    GRAY_DARK = "
class GradientColors:
    PURPLE_GRADIENT = f"linear-gradient(135deg, {PrimaryColors.PURPLE_LIGHT} 0%, {PrimaryColors.PURPLE_DARK} 100%)"
    ACCENT_GRADIENT = f"linear-gradient(135deg, {SecondaryColors.BLUE_ACCENT} 0%, {PrimaryColors.PURPLE_PRIMARY} 100%)"
    NEUTRAL_GRADIENT = f"linear-gradient(135deg, {SecondaryColors.GRAY_LIGHT} 0%, {SecondaryColors.GRAY_MEDIUM} 100%)"
class Typography:
    HEADING_1_SIZE = "32px"
    HEADING_2_SIZE = "24px"
    HEADING_3_SIZE = "20px"
    HEADING_4_SIZE = "18px"
    BODY_SIZE = "16px"
    SMALL_SIZE = "14px"
    CAPTION_SIZE = "12px"
    BOLD = 700
    SEMIBOLD = 600
    MEDIUM = 500
    REGULAR = 400
    LIGHT = 300
    TIGHT = 1.2
    NORMAL = 1.5
    LOOSE = 1.8
class StatusIndicators(Enum):
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
        return cls.COLORS.get(status, SecondaryColors.GRAY_MEDIUM)
    @classmethod
    def get_status_display(cls, status: str) -> str:
        try:
            indicator = StatusIndicators(status)
            color = cls.get_color(indicator)
            return f"{indicator.value}"
        except ValueError:
            return status
class MessageTemplates:
    SUCCESS_CREATED = "{resource} created successfully"
    SUCCESS_UPDATED = "{resource} updated successfully"
    SUCCESS_DELETED = "{resource} deleted successfully"
    SUCCESS_PROCESSED = "{action} completed successfully"
    ERROR_NOT_FOUND = "{resource} not found"
    ERROR_INVALID_INPUT = "Invalid input provided"
    ERROR_UNAUTHORIZED = "Unauthorized access"
    ERROR_FORBIDDEN = "Access forbidden"
    ERROR_SERVER_ERROR = "An error occurred while processing your request"
    ERROR_VALIDATION = "Validation failed: {details}"
    ERROR_CONFLICT = "Resource conflict: {details}"
    NOTIFY_MINTING_STARTED = "NFT minting has started"
    NOTIFY_MINTING_COMPLETE = "NFT has been minted successfully"
    NOTIFY_LISTING_CREATED = "NFT has been listed for sale"
    NOTIFY_OFFER_RECEIVED = "You have received an offer"
    NOTIFY_TRANSACTION_CONFIRMED = "Transaction confirmed"
    NOTIFY_WALLET_CREATED = "Wallet created successfully"
    @classmethod
    def format_success(cls, action: str, resource: str) -> str:
        return f"{resource} {action} successfully"
    @classmethod
    def format_error(cls, error_type: str, details: str = "") -> str:
        messages = {
            "not_found": f" not found",
            "invalid": f"Invalid input",
            "unauthorized": f"Unauthorized access",
            "server_error": f"Server error occurred",
        }
        base = messages.get(error_type, "An error occurred")
        return f"{base}: {details}" if details else base
class Spacing:
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"
class BorderRadius:
    NONE = "0px"
    SM = "4px"
    MD = "8px"
    LG = "12px"
    FULL = "9999px"
class Elevation:
    NONE = "0 0 0 0 rgba(0,0,0,0)"
    SM = "0 1px 2px 0 rgba(0,0,0,0.05)"
    MD = "0 4px 6px -1px rgba(0,0,0,0.1)"
    LG = "0 10px 15px -3px rgba(0,0,0,0.1)"
    XL = "0 20px 25px -5px rgba(0,0,0,0.1)"
    XXL = "0 25px 50px -12px rgba(0,0,0,0.25)"
class ResponseFormat(NamedTuple):
    success: bool
    status_code: int
    title: str
    message: str
    data: dict = None
    timestamp: str = None
class HTTPStatusCodes:
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
        return cls.MESSAGES.get(code, "Unknown Status")
LOG_FORMAT_STANDARD = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
LOG_FORMAT_DETAILED = "[%(asctime)s] %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_FORMAT_JSON = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
