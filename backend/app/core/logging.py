import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO"):
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Silence overly verbose external loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


def get_logger(name: str, job_id: Optional[str] = None, video_id: Optional[str] = None) -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    extra = {
        "job_id": job_id or "-",
        "video_id": video_id or "-"
    }
    return logging.LoggerAdapter(logger, extra)

