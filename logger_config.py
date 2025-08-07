import logging
import sys
from pathlib import Path
from datetime import datetime

# Get current date string
date_str = datetime.now().strftime("%Y-%m-%d")

# Log file path
log_path = Path(__file__).resolve().parent / f"logs/python_{date_str}.log"
# 🔧 Ensure logs directory exists
log_path.parent.mkdir(parents=True, exist_ok=True)
# Configure logger
logger = logging.getLogger("my_app_logger")
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# ✅ Catch uncaught exceptions globally
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Let KeyboardInterrupt go through
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception
