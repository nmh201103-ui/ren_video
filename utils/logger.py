import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
_logger_setup = False


def setup_logger():
    """Setup logger với format giống Laravel.log"""
    global _logger_setup
    if _logger_setup:
        return
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Format giống Laravel: [YYYY-MM-DD HH:MM:SS] channel.LEVEL: message
    log_format = "[%(asctime)s] %(name)s.%(levelname)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # File handler với append mode
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Root logger
    root_logger = logging.getLogger("affiliate_video_creator")
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    root_logger.propagate = False
    
    _logger_setup = True


def get_logger(name: str = "affiliate_video_creator") -> logging.Logger:
    """Get logger, tự động setup nếu chưa được setup"""
    if not _logger_setup:
        setup_logger()
    return logging.getLogger(name)


