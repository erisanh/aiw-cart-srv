import json
import logging
import os
from logging.handlers import RotatingFileHandler

import colorlog
from app.core.config import settings


class UTF8JSONFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            record.msg = json.dumps(record.msg, ensure_ascii=False)
        elif isinstance(record.msg, str):
            try:
                # Attempt to decode the message as JSON
                json_msg = json.loads(record.msg)
                record.msg = json.dumps(json_msg, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                # If it's not valid JSON, leave it as is
                pass
        return super().format(record)


def setup_logger() -> logging.Logger:
    logger = colorlog.getLogger(__name__)

    # Only add handlers if the logger doesn't have any
    if not logger.handlers:
        # Console handler
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)s:%(name)s:%(pathname)s:%(funcName)s:%(lineno)d:%(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                    "EXCEPTION": "purple",
                },
            )
        )
        logger.addHandler(console_handler)

        # File handler
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "log"
        )
        os.makedirs(log_dir, exist_ok=True)

        if settings.ENV == "local":
            log_file = os.path.join(log_dir, "local.log")
        else:
            log_file = os.path.join(log_dir, "dev.log")

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(
            UTF8JSONFormatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

        logger.setLevel(logging.DEBUG)

    return logger