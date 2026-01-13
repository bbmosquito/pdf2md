"""
Logging configuration and utilities.

Provides structured logging for the PDF2MD application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_COLOR = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s"

# Color codes for terminal output
class LogColors:
    """ANSI color codes for log levels."""
    RESET = "\033[0m"
    DEBUG = "\033[36m"    # Cyan
    INFO = "\033[32m"     # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"    # Red
    CRITICAL = "\033[35m" # Magenta


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def __init__(self, fmt: str, use_colors: bool = True):
        """Initialize colored formatter."""
        super().__init__(fmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if self.use_colors:
            color = self.COLORS.get(record.levelno, "")
            record.log_color = color
            record.reset = LogColors.RESET
        else:
            record.log_color = ""
            record.reset = ""

        # Format the message
        result = super().format(record)

        # Add reset if using colors
        if self.use_colors:
            result += LogColors.RESET

        return result


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str | Path] = None,
    console: bool = True,
    use_colors: bool = True
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console: Whether to log to console
        use_colors: Whether to use colors in console output

    Returns:
        The root logger
    """
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)

        # Check if we should use colors (only on TTY)
        actual_use_colors = use_colors and sys.stdout.isatty()

        console_formatter = ColoredFormatter(
            LOG_FORMAT if not actual_use_colors else LOG_FORMAT_COLOR,
            use_colors=actual_use_colors
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)

        # No colors in file
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class ProgressLogger:
    """
    Context manager for logging progress of operations.

    Usage:
        with ProgressLogger(logger, "Processing file", "file.pdf") as progress:
            # Do work
            progress.update(50, "Half done")
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        target: str = "",
        level: int = logging.INFO
    ):
        """
        Initialize progress logger.

        Args:
            logger: Logger instance
            operation: Description of the operation
            target: Target of the operation (e.g., filename)
            level: Log level to use
        """
        self.logger = logger
        self.operation = operation
        self.target = target
        self.level = level
        self._start_time = None

    def _format_message(self, message: str = "") -> str:
        """Format log message with operation and target."""
        parts = [self.operation]
        if self.target:
            parts.append(f"'{self.target}'")
        if message:
            parts.append(f"- {message}")
        return " ".join(parts)

    def __enter__(self):
        """Enter context, log start message."""
        self._start_time = datetime.now()
        self.logger.log(self.level, self._format_message("started"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context, log completion message."""
        duration = datetime.now() - self._start_time
        duration_str = self._format_duration(duration)

        if exc_type is None:
            self.logger.log(
                self.level,
                self._format_message(f"completed in {duration_str}")
            )
        else:
            self.logger.error(
                self._format_message(f"failed after {duration_str}: {exc_val}")
            )
        return False

    def update(self, progress: int = None, message: str = "") -> None:
        """
        Log a progress update.

        Args:
            progress: Progress percentage (0-100)
            message: Optional message
        """
        parts = [self._format_message(message)]
        if progress is not None:
            parts.append(f"({progress}%)")
        self.logger.log(self.level, " ".join(parts))

    @staticmethod
    def _format_duration(delta) -> str:
        """Format a timedelta as a readable string."""
        seconds = delta.total_seconds()

        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
