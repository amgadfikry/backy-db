# tests/logger/test_logger_manager.py
import logging
import os
from pathlib import Path
from logger.logger_manager import LoggerManager


class TestLoggerManager:
    """
    Test suite for LoggerManager class.
    """

    def test_logger_creation_with_file_and_console_handler(self):
        """
        Test that a logger is created with both file and console handlers.
        """
        logger = LoggerManager.setup_logger(name="test_logger", log_file="test_log")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        handler_types = {type(h) for h in logger.handlers}
        assert logging.StreamHandler in handler_types
        assert logging.FileHandler in handler_types

    def test_logger_does_not_duplicate_handlers(self):
        """
        Test that a logger does not duplicate handlers when created multiple times with the same name.
        """
        logger1 = LoggerManager.setup_logger(name="dup_logger", log_file="dup_log")
        handlers_before = len(logger1.handlers)
        logger2 = LoggerManager.setup_logger(name="dup_logger", log_file="dup_log")
        handlers_after = len(logger2.handlers)
        assert logger1 is logger2
        assert handlers_before == handlers_after

    def test_logger_logs_to_file(self):
        """
        Test that a logger logs messages to a file.
        """
        logger = LoggerManager.setup_logger(name="file_test", log_file="mylogfile")
        logger.info("Test log message")
        log_file_path = Path(os.getenv("LOGGING_PATH")) / "mylogfile.log"
        assert log_file_path.exists()
        content = log_file_path.read_text()
        assert "Test log message" in content
        assert "INFO" in content

    def test_logger_level_respected(self):
        """
        Test that the logger respects the specified logging level.
        """
        logger = LoggerManager.setup_logger(
            name="level_test", log_file="lvl", level=logging.ERROR
        )
        assert logger.level == logging.ERROR

    def test_logger_cache_returns_same_logger(self):
        """
        Test that the logger cache returns the same logger instance for the same name.
        """
        logger1 = LoggerManager.setup_logger(name="cached", log_file="cached_log")
        logger2 = LoggerManager.setup_logger(name="cached", log_file="cached_log")
        assert logger1 is logger2
