import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# find Root dir (Multi-Agent-TourAI)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"