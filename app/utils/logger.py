import logging
import logging.config
import sys
logger = logging.getLogger("app")
_bootstrap_handler = logging.StreamHandler(sys.stdout)
_bootstrap_handler.setLevel(logging.DEBUG)
_bootstrap_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_bootstrap_handler.setFormatter(_bootstrap_formatter)
logger.addHandler(_bootstrap_handler)
logger.setLevel(logging.DEBUG)
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
def configure_logging():
    try:
        from app.config import get_settings
        settings = get_settings()
    except Exception as e:
        logger.warning(
            f"Could not load settings for detailed logging config: {e}. "
            "Using bootstrap configuration."
        )
        return
    
    # Get log level from settings, default to DEBUG to capture all logs
    log_level = getattr(settings, "log_level", "DEBUG").upper()
    environment = getattr(settings, "environment", "development")
    
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
                "level": "DEBUG",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": True,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handler for non-production environments
    if environment != "production":
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 5,
        }
        config["root"]["handlers"].append("file")
        config["loggers"]["app"]["handlers"].append("file")
    
    logging.config.dictConfig(config)
    logger.info(f"Logging configured - Level: {log_level}, Environment: {environment}")
