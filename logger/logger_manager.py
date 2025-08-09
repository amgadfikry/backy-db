# logger/logger_manager.py
import logging
import sys
import os
from pathlib import Path
from typing import Union
from dotenv import load_dotenv

load_dotenv()


class LoggerManager:
    """
    A class to manage logging setup for the application.
    This class provides a method to set up a logger with specified configurations.
    """

    __logger_cache = {}

    @staticmethod
    def setup_logger(
        name: str = "backydb", log_file: Union[str, Path] = None, level=logging.WARNING
    ) -> logging.Logger:
        """
        Set up a logger with the specified name and log file.
        If no log file is specified, logs will only be printed to the console.
        Args:
            name (str): The name of the logger.
            log_file (Union[str, Path]): Optional path to or name of a log file
            level (int): Logging level (default is DEBUG).
        Returns:
            logging.Logger: Configured logger instance.
        """
        # Create a path for the logging directory
        log_path = Path.home() / Path(os.getenv("LOGGING_PATH", ".backy/logs"))
        log_path.mkdir(parents=True, exist_ok=True)

        # Construct full log file path with log file name or default to logger name
        stem = Path(log_file).stem if log_file else name
        log_file_path = log_path / f"{stem}.log"

        # Cache key based on both name and log file
        cache_key = f"{name}:{log_file_path}"
        if cache_key in LoggerManager.__logger_cache:
            return LoggerManager.__logger_cache[cache_key]

        # Create a logger and set its level
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Avoid adding handlers multiple times
        if not logger.handlers:
            # Add console handler
            logger.addHandler(LoggerManager.__console_handler(level))
            # Add file handler
            logger.addHandler(LoggerManager.__file_handler(log_file_path, level))

        LoggerManager.__logger_cache[cache_key] = logger
        return logger

    @staticmethod
    def __console_handler(level: int) -> logging.StreamHandler:
        """
        Create a console handler for the logger.
        Args:
            level (int): Logging level for the console handler.
        Returns:
            logging.StreamHandler: Configured console handler.
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        return console_handler

    @staticmethod
    def __file_handler(log_file: Path, level: int) -> logging.FileHandler:
        """
        Create a file handler for the logger.
        Args:
            log_file (Path): Path to the log file.
            level (int): Logging level for the file handler.
        Returns:
            logging.FileHandler: Configured file handler.
        """
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        return file_handler
