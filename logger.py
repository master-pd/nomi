"""
Logger System - Centralized logging
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import colorlog

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        return json.dumps(log_data, ensure_ascii=False)

class NOMILogger:
    """Custom logger for NOMI bot"""
    
    def __init__(self):
        self.loggers = {}
        self.setup_done = False
        
    def setup_logging(self, log_level: str = "INFO", log_to_file: bool = True):
        """
        Setup logging configuration
        
        Args:
            log_level: Logging level
            log_to_file: Whether to log to file
        """
        if self.setup_done:
            return
            
        # Create logs directory
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Console handler with colors
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        if log_to_file:
            # Regular log file
            file_handler = logging.handlers.RotatingFileHandler(
                'data/logs/nomi_bot.log',
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            # JSON log file for structured logging
            json_handler = logging.handlers.RotatingFileHandler(
                'data/logs/nomi_bot.json.log',
                maxBytes=10*1024*1024,
                backupCount=3,
                encoding='utf-8'
            )
            json_formatter = JSONFormatter()
            json_handler.setFormatter(json_formatter)
            root_handler = logging.getLogger('nomi_json')
            json_handler.setLevel(logging.INFO)
            root_handler.addHandler(json_handler)
            
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            'data/logs/errors.log',
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        self.setup_done = True
        logging.info("📝 Logging system initialized")
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
            
        return self.loggers[name]
        
    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """
        Log structured event
        
        Args:
            event_type: Type of event
            data: Event data
            level: Log level
        """
        logger = self.get_logger('nomi_events')
        
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **data
        }
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(json.dumps(log_data, ensure_ascii=False))
        
    def log_performance(self, operation: str, duration: float, 
                       data: Dict[str, Any] = None):
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            data: Additional data
        """
        logger = self.get_logger('nomi_performance')
        
        perf_data = {
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        if data:
            perf_data.update(data)
            
        if duration > 1.0:
            logger.warning(f"⏱️ Slow operation: {operation} took {duration:.2f}s")
        elif duration > 0.5:
            logger.info(f"⏱️ Operation: {operation} took {duration:.2f}s")
        else:
            logger.debug(f"⏱️ Operation: {operation} took {duration:.3f}s")
            
    def log_command(self, user_id: int, command: str, 
                   group_id: Optional[int] = None, success: bool = True):
        """
        Log command usage
        
        Args:
            user_id: User ID
            command: Command used
            group_id: Group ID
            success: Whether command succeeded
        """
        logger = self.get_logger('nomi_commands')
        
        log_data = {
            'user_id': user_id,
            'command': command,
            'group_id': group_id,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(json.dumps(log_data, ensure_ascii=False))
        
    def log_error(self, error: Exception, context: str = "", 
                 extra_data: Dict[str, Any] = None):
        """
        Log error with context
        
        Args:
            error: Exception object
            context: Error context
            extra_data: Additional data
        """
        logger = self.get_logger('nomi_errors')
        
        error_data = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if extra_data:
            error_data.update(extra_data)
            
        logger.error(json.dumps(error_data, ensure_ascii=False))
        
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        log_files = list(Path("data/logs").glob("*.log"))
        
        stats = {
            'total_log_files': len(log_files),
            'log_files': [],
            'active_loggers': len(self.loggers)
        }
        
        for log_file in log_files:
            try:
                size = log_file.stat().st_size
                stats['log_files'].append({
                    'name': log_file.name,
                    'size_mb': size / (1024 * 1024)
                })
            except:
                pass
                
        return stats

# Global logger instance
nomi_logger = NOMILogger()

def setup_logger(name: str = "nomi") -> logging.Logger:
    """
    Setup and get logger
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    nomi_logger.setup_logging()
    return nomi_logger.get_logger(name)