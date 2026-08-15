"""Minimal structured JSON logging — one machine-parseable line per event.

Correlation IDs (sos_id etc.) are attached by the API layer in later phases;
this module only guarantees the shape every log line has.
"""

import json
import logging
import sys
from datetime import UTC, datetime

_configured = False


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for key in ("sos_id", "env", "path", "status"):
            if key in record.__dict__:
                payload[key] = str(record.__dict__[key])
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # uvicorn's access log duplicates what our request logs will carry.
    logging.getLogger("uvicorn.access").handlers = []
    _configured = True
