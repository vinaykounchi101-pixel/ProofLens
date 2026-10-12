"""Structured logging configuration with correlation ID support and secret redaction."""

import json
import logging
import sys
from typing import Any, Dict


class SafeJsonFormatter(logging.Formatter):
    """Custom JSON formatter that redacts secrets and formats log entries as structured JSON."""

    SENSITIVE_KEYS = {"api_key", "secret", "password", "token", "authorization"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach request_id if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Redact sensitive data from extra dict
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            safe_extra = {}
            for k, v in record.extra.items():
                if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                    safe_extra[k] = "[REDACTED]"
                else:
                    safe_extra[k] = v
            log_entry["extra"] = safe_extra

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SafeJsonFormatter())
    root_logger.addHandler(console_handler)

    # Suppress overly chatty 3rd party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.WARNING)


logger = logging.getLogger("prooflens")
