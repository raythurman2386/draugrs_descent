import logging
import os
import datetime
import sys
from logging.handlers import RotatingFileHandler

# Log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Default format settings
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Default log file with timestamp
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, f"game_{current_time}.log")


class GameLogger:
    """
    Custom logger for the game that provides consistent formatting and behavior.
    """

    _loggers = {}  # Cache to store created loggers

    @staticmethod
    def get_logger(
        name,
        level=DEBUG,
        log_to_file=True,
        log_to_console=True,
        file_path=DEFAULT_LOG_FILE,
        max_file_size=5 * 1024 * 1024,
        backup_count=3,
        format_string=DEFAULT_FORMAT,
    ):
        """
        Get or create a logger with the specified name and configuration.

        Args:
            name: Name of the logger (typically module name)
            level: Logging level (DEBUG, INFO, etc.)
            log_to_file: Whether to log to a file
            log_to_console: Whether to log to console
            file_path: Path to log file
            max_file_size: Maximum size of log file before rotating
            backup_count: Number of backup log files to keep
            format_string: Format string for log messages

        Returns:
            Logger instance
        """
        # Return existing logger if already created
        if name in GameLogger._loggers:
            return GameLogger._loggers[name]

        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False  # Don't propagate to parent loggers

        # Clear existing handlers if any
        if logger.handlers:
            logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(format_string)

        # Add file handler if needed
        if log_to_file:
            file_handler = RotatingFileHandler(
                file_path, maxBytes=max_file_size, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Add console handler if needed
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # Cache the logger
        GameLogger._loggers[name] = logger
        return logger

    @staticmethod
    def set_all_loggers_level(level):
        """Set the level for all existing loggers."""
        for logger in GameLogger._loggers.values():
            logger.setLevel(level)


# Example usage
if __name__ == "__main__":
    # Create a logger for testing
    logger = GameLogger.get_logger("test")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
