# storage/storage_base.py
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv
import os
from logger.logger_manager import LoggerManager

load_dotenv()


class StorageBase(ABC):
    """
    Base class for all storage implementations in the Backy project.
    This class defines the common interface and methods that all storage
    classes should implement.
    """
    def __init__(self, config: dict):
        """
        Initialize the storage with the given configuration.
        Args:
            config: Configuration dictionary for the storage.
        """
        self.logger = LoggerManager.setup_logger("storage")
        self.storage_type = config.get("storage_type", "local")
        self.path = Path(config.get("path", None))
        if not self.path or not self.path.exists():
            self.logger.error("Storage path is not set or does not exist.")
            raise ValueError("Storage path is not set or does not exist.")
        self.processed_path = Path(os.getenv('MAIN_BACKUP_PATH', None))
        if not self.processed_path or not self.processed_path.exists():
            self.logger.error("MAIN_BACKUP_PATH environment variable is not set.")
            raise ValueError("MAIN_BACKUP_PATH environment variable is not set.")

    @abstractmethod
    def upload(self) -> Path:
        """
        Upload a file from local path to remote storage.
        """
        self.logger.error(f"Upload method not implemented in {self.__class__.__name__}")
        raise NotImplementedError(f"Upload method not implemented in {self.__class__.__name__}")

    @abstractmethod
    def download(self) -> Path:
        """
        Download a file from remote storage to the local path.
        """
        self.logger.error(f"Download method not implemented in {self.__class__.__name__}")
        raise NotImplementedError(f"Download method not implemented in {self.__class__.__name__}")
