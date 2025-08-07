# core/integrity/integrity_base.py
from pathlib import Path
import os
from dotenv import load_dotenv
from logger.logger_manager import LoggerManager
from abc import ABC, abstractmethod

load_dotenv()


class IntegrityBase(ABC):
    """
    Base class for integrity operations, providing common functionality.
    """

    def __init__(self):
        """
        Initialize the IntegrityBase with necessary configurations.
        """
        self.logger = LoggerManager.setup_logger("integrity")
        self.processing_path = Path(os.getenv("MAIN_BACKUP_PATH"))

    @abstractmethod
    def create_integrity(self) -> Path:
        """
        Abstract method to create integrity file.
        This method should be implemented by subclasses.
        Returns:
            Path: The path to the created integrity file.
        """
        self.logger.error("create_integrity method not implemented.")
        raise NotImplementedError("create_integrity method not implemented.")

    @abstractmethod
    def verify_integrity(self, integrity_file: Path) -> bool:
        """
        Abstract method to verify integrity.
        This method should be implemented by subclasses.
        Args:
            integrity_file (Path): The path to the integrity file to verify.
        Returns:
            bool: True if integrity is verified, False otherwise.
        """
        self.logger.error("verify_integrity method not implemented.")
        raise NotImplementedError("verify_integrity method not implemented.")

    def check_path(self, path: Path) -> None:
        """
        Check if the given path is valid and exists.
        Args:
            path (Path): The path to check.
        """
        if not path.exists():
            self.logger.error(f"Path {path} does not exist.")
            raise FileNotFoundError(f"Path {path} does not exist.")
        if not path.is_file():
            self.logger.error(f"Path {path} is not a file.")
            raise FileNotFoundError(f"Path {path} is not a file.")

    def get_files_from_processing_path(self) -> list[Path]:
        """
        Get all files from the processing path.
        Returns:
            list[Path]: A list of Path objects representing files in the processing path.
        """
        files = sorted(self.processing_path.glob("*"))
        files = [file for file in files if file.is_file()]
        if not files:
            self.logger.error("No files found in the processing path.")
            raise FileNotFoundError("No files found in the processing path.")
        return files
