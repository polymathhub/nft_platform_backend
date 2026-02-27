import logging
import logging.config
import sys

# ✅ CRITICAL: Create logger IMMEDIATELY without dependencies
# This ensures the module can always be imported, even if settings fail
logger = logging.getLogger("app")

# Minimal bootstrap handler to stdout - used until configure_logging() is called
_bootstrap_handler = logging.StreamHandler(sys.stdout)
_bootstrap_handler.setLevel(logging.DEBUG)
_bootstrap_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_bootstrap_handler.setFormatter(_bootstrap_formatter)
logger.addHandler(_bootstrap_handler)
logger.setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name.
    
    Safe to call at any time, even before configure_logging().
    """
    return logging.getLogger(name)


def configure_logging():
    """Configure detailed logging when settings are available.
    
    This is called AFTER app.config is successfully loaded.
    Uses Railway-safe stdout/stderr handlers for container environments.
    """
    try:
        from app.config import get_settings
        settings = get_settings()
    except Exception as e:
        logger.warning(
            f"Could not load settings for detailed logging config: {e}. "
            "Using bootstrap configuration."
        )
        return

    # Build dynamic config with loaded settings
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": getattr(settings, "log_level", "INFO"),
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": getattr(settings, "log_level", "INFO"),
            "handlers": ["console"],
        },
        "loggers": {
            "app": {
                "level": getattr(settings, "log_level", "INFO"),
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Only add file handler if not running in production/container environment
    environment = getattr(settings, "environment", "development")
    if environment != "production":
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": getattr(settings, "log_level", "INFO"),
            "formatter": "detailed",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 5,
        }
        config["root"]["handlers"].append("file")
        config["loggers"]["app"]["handlers"].append("file")

    logging.config.dictConfig(config)




