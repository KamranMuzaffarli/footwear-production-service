import logging

from app.core.config import settings

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )
