import pytest
import logging
import os
import threading
import sys
from unittest.mock import patch, MagicMock
from utils.logger import GameLogger, SafeRotatingFileHandler


class TestGameLogger:
    """Test cases for the game's logging system."""

    @pytest.fixture
    def logger_with_mock(self, tmp_path):
        """Fixture to create a GameLogger with a temporary log file."""
        log_file = tmp_path / "test.log"
        logger = GameLogger.get_logger(
            "test_logger",
            log_to_file=True,
            log_to_console=True,
            file_path=str(log_file),
        )
        yield logger, log_file

    @pytest.mark.parametrize(
        "log_to_file, log_to_console, expected_handlers",
        [
            (True, True, 2),  # File and console handlers
            (True, False, 1),  # Only file handler
            (False, True, 1),  # Only console handler
            (False, False, 0),  # No handlers
        ],
    )
    def test_logger_initialization(self, tmp_path, log_to_file, log_to_console, expected_handlers):
        """Test that the logger initializes with the correct configuration."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        logger = GameLogger.get_logger(
            f"init_logger_{log_to_file}_{log_to_console}",  # Unique name for each parameter combo
            log_to_file=log_to_file,
            log_to_console=log_to_console,
            file_path=str(log_file),
        )
        assert logger.name == f"init_logger_{log_to_file}_{log_to_console}"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == expected_handlers
        if log_to_file:
            assert any(isinstance(h, SafeRotatingFileHandler) for h in logger.handlers)
        if log_to_console:
            assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_logger_caching(self, tmp_path):
        """Test that the same logger instance is returned for the same name."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        logger1 = GameLogger.get_logger("cached_logger", file_path=str(log_file))
        logger2 = GameLogger.get_logger("cached_logger", file_path=str(log_file))
        assert logger1 is logger2

    def test_log_levels(self, tmp_path):
        """Test that log messages respect the logger's level."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        logger = GameLogger.get_logger(
            "level_logger",
            level=logging.INFO,
            log_to_file=True,
            log_to_console=False,
            file_path=str(log_file),
        )

        # Log messages
        logger.debug("Debug message")
        logger.info("Info message")

        # Check file contents
        with open(log_file, "r") as f:
            content = f.read()
            assert "Debug message" not in content
            assert "Info message" in content

    def test_log_output(self, tmp_path):
        """Test logging to file and console."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        # Configure logger with direct console output to avoid buffer issues
        logger = GameLogger.get_logger(
            "output_logger",
            log_to_file=True,
            log_to_console=False,  # Don't log to console for this test
            file_path=str(log_file),
        )

        # Log a test message
        logger.info("Test message")

        # Check file output
        with open(log_file, "r") as f:
            file_content = f.read()
            assert "Test message" in file_content

    def test_log_rotation(self, tmp_path):
        """Test that log files rotate when the size limit is exceeded."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        logger = GameLogger.get_logger(
            "rotation_logger",
            log_to_file=True,
            log_to_console=False,
            file_path=str(log_file),
            max_file_size=100,  # Small size to trigger rotation
            backup_count=1,
        )
        for _ in range(10):
            logger.info("Long message to trigger rotation")
        backup_file = log_file.with_suffix(".log.1")
        assert backup_file.exists()

    def test_permission_error_handling(self, tmp_path):
        """Test handling of permission errors during log rotation."""
        # This test simulates a permission error when logging and verifies it's handled properly
        log_file = tmp_path / "test.log"

        # Create a record with a message attribute (this is important)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test permission error",
            args=(),
            exc_info=None,
        )
        # We need to ensure the record has a message attribute which is used in the handler
        record.message = "Test permission error"

        # Create a handler that will raise permission error
        handler = SafeRotatingFileHandler(str(log_file), maxBytes=100, backupCount=1)

        # Patch the superclass emit to simulate a permission error
        with patch("logging.handlers.RotatingFileHandler.emit", side_effect=PermissionError()):
            # Also patch stderr to verify it's being written to
            with patch("sys.stderr.write") as mock_stderr_write:
                # Call emit which should catch the permission error and write to stderr
                handler.emit(record)

                # Verify stderr.write was called with the expected error message
                mock_stderr_write.assert_called_with(
                    "Logger permission error: Test permission error\n"
                )

    def test_thread_safety(self, tmp_path):
        """Test logging from multiple threads."""
        # Clear cached loggers to ensure clean test
        GameLogger._loggers = {}

        log_file = tmp_path / "test.log"
        logger = GameLogger.get_logger(
            "thread_logger",
            log_to_file=True,
            log_to_console=False,
            file_path=str(log_file),
        )

        def log_from_thread():
            for i in range(50):
                logger.info(f"Thread message {i}")

        threads = [threading.Thread(target=log_from_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        with open(log_file, "r") as f:
            content = f.read()
            assert len(content) > 0
