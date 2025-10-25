import logging
import os
from pathlib import Path

# ANSI color codes for console output
COLORS = {
    'DEBUG': '\033[38;2;127;127;127m',    # gray
    'INFO': '\033[38;2;255;255;0m',       # yellow
    'WARNING': '\033[38;2;255;95;0m',     # orange
    'ERROR': '\033[38;2;255;0;0m',        # red
    'CRITICAL': '\033[1m\033[38;2;255;0;0m',  # bold red
}
BOLD = '\033[1m'
GRAY = '\033[38;2;127;127;127m'
CYAN = '\033[38;2;0;255;255m'
RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output"""
    
    def format(self, record):
        # Add color based on log level
        levelcolor = COLORS.get(record.levelname, '')
        
        # Format: [TIMESTAMP] LEVEL - [module] message
        # Using colored level and gray prefix
        log_fmt = f"{GRAY}[%(asctime)s]{RESET} {levelcolor}%(levelname)-8s{RESET} {GRAY}[%(name)s]{RESET} %(message)s"
        
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logging():
    """Configure logging for FrigBot"""
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create handlers
    file_handler = logging.FileHandler('logs/frigbot.log', encoding='utf-8')
    console_handler = logging.StreamHandler()

    # Set formatters
    # Plain format for file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Colored format for console
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Return logger for main module
    return logging.getLogger('frigbot')

