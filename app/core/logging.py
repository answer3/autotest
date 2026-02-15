import os
import sys

from loguru import logger

from app.core.config import settings

_CONFIGURED = False


def setup_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    logger.remove()

    level = settings.log_level.upper()
    log_file = settings.log_file

    fmt = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}"

    logger.add(sys.stdout, level=level, format=fmt)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logger.add(
            log_file,
            level=level,
            format=fmt,
            rotation="10 MB",
            retention="14 days",
            compression="zip",
        )
