"""Logging configuration for Alumni Tracking System.

Configures:
- Console stream handler for standard request/info logs.
- Dedicated file handler writing errors (ERROR and CRITICAL) with full
  tracebacks to logs/error.log.
"""

import logging
import sys
from pathlib import Path

# Resolve project root directory (/Users/.../alumni-tracking-system)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
ERROR_LOG_PATH = LOGS_DIR / "error.log"

_is_configured = False


def setup_logging():
    """Initializes logging handlers and formatters."""
    global _is_configured
    if _is_configured:
        return

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Standard formatters
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler for INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # File Handler specifically for ERROR and CRITICAL
    error_file_handler = logging.FileHandler(str(ERROR_LOG_PATH), encoding="utf-8")
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)

    # Configure root and app loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicate log entries
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_file_handler)

    # Specific logger for HTTP request logging middleware
    request_logger = logging.getLogger("app.middleware.request")
    request_logger.setLevel(logging.INFO)

    # Specific logger for application server errors
    error_logger = logging.getLogger("app.error")
    error_logger.setLevel(logging.ERROR)

    _is_configured = True


# Initialize on import so logging is active across all entrypoints and tests
setup_logging()
