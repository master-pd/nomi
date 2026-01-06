"""
Advanced Logging System
For comprehensive logging with different levels, file rotation, and formatting
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any

from config import Config

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Call original formatter
        return super().format(record)

class BotLogger:
    """Professional logging system for the bot"""
    
    def __init__(self, name: str = "your_crush_bot"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
        
        # Disable propagation to root logger
        self.logger.propagate = False
    
    def _setup_handlers(self):
        """Setup all logging handlers"""
        
        # 1. Console Handler (Colored)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_format = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # 2. File Handler (Daily rotation)
        log_dir = os.path.join(Config.BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "bot.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # 3. Error File Handler (Errors only)
        error_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "error.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        error_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
        )
        error_handler.setFormatter(error_format)
        
        # 4. Performance Handler
        perf_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, "performance.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda record: record.name.endswith('.performance'))
        
        perf_format = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        perf_handler.setFormatter(perf_format)
        
        # Add all handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(perf_handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """Debug level logging"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Info level logging"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Warning level logging"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Error level logging"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Critical level logging"""
        self.logger.critical(msg, *args, **kwargs)
    
    def log_performance(self, operation: str, duration: float, details: Dict = None):
        """Log performance metrics"""
        perf_logger = logging.getLogger(f"{self.name}.performance")
        
        details_str = ""
        if details:
            details_str = " - " + " ".join(f"{k}={v}" for k, v in details.items())
        
        perf_logger.info(f"{operation} - {duration:.3f}s{details_str}")
    
    def log_user_action(self, user_id: int, action: str, details: Dict = None):
        """Log user actions"""
        details_str = ""
        if details:
            details_str = " - " + " ".join(f"{k}={v}" for k, v in details.items())
        
        self.info(f"USER_{user_id} - {action}{details_str}")
    
    def log_group_action(self, group_id: int, action: str, details: Dict = None):
        """Log group actions"""
        details_str = ""
        if details:
            details_str = " - " + " ".join(f"{k}={v}" for k, v in details.items())
        
        self.info(f"GROUP_{group_id} - {action}{details_str}")
    
    def log_system_event(self, event: str, details: Dict = None):
        """Log system events"""
        details_str = ""
        if details:
            details_str = " - " + " ".join(f"{k}={v}" for k, v in details.items())
        
        self.info(f"SYSTEM - {event}{details_str}")
    
    def get_log_stats(self, days: int = 7) -> Dict:
        """Get logging statistics"""
        try:
            log_dir = os.path.join(Config.BASE_DIR, "logs")
            stats = {
                "total_size": 0,
                "file_counts": {},
                "recent_errors": 0,
                "log_levels": {}
            }
            
            if not os.path.exists(log_dir):
                return stats
            
            # Count files and sizes
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    size = os.path.getsize(filepath)
                    
                    stats["file_counts"][filename] = size
                    stats["total_size"] += size
            
            return stats
            
        except Exception as e:
            self.error(f"Error getting log stats: {e}")
            return {}

def setup_logger(name: str = "your_crush_bot") -> BotLogger:
    """
    Setup and return a configured logger
    """
    return BotLogger(name)

# Global logger instance
logger = setup_logger()