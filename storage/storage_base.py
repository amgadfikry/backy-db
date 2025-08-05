# storage/storage_base.py
from abc import ABC, abstractmethod
from pathlib import Path
from logger.logger_manager import LoggerManager


class StorageBase(ABC):
    """
    Base class for all storage implementations in the Backy project.
    This class defines the common interface and methods that all storage
    classes should implement.
    """

    def __init__(self, db_name: str = "backy_db"):
        """
        Initialize the storage with the given configuration.
        Args:
            config: Configuration dictionary for the storage.
        """
        self.db_name = db_name
        self.logger = LoggerManager.setup_logger("storage")

    @abstractmethod
    def upload(self, file_path: str) -> str:
        """
        Upload a file from local path to remote storage.
        Args:
            file_path (str): The path to the file to be uploaded.
        Returns:
            str: The path to the uploaded file in remote storage.
        """
        self.logger.error(f"Upload method not implemented in {self.__class__.__name__}")
        raise NotImplementedError(
            f"Upload method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    def download(self, file_path: str) -> str:
        """
        Download a file from remote storage to the local path.
        Args:
            file_path (str): The path to the file to be downloaded.
        Returns:
            str: The path to the downloaded file in local storage.
        """
        self.logger.error(
            f"Download method not implemented in {self.__class__.__name__}"
        )
        raise NotImplementedError(
            f"Download method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate the credentials for the storage.
        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        self.logger.error(
            f"Validate credentials method not implemented in {self.__class__.__name__}"
        )
        raise NotImplementedError(
            f"Validate credentials method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    def delete(self, file_path: str) -> None:
        """
        Delete a file from remote storage.
        Args:
            file_path (str): The path to the file to be deleted.
        """
        self.logger.error(f"Delete method not implemented in {self.__class__.__name__}")
        raise NotImplementedError(
            f"Delete method not implemented in {self.__class__.__name__}"
        )

    def generate_dest_path(self, file_path: str) -> str:
        """
        Generate a destination path for the file based on the database name and current timestamp.
        Args:
            file_path (str): The path to the file.
        Returns:
            str: The generated destination path.
        """
        db_name = self.db_name.replace(" ", "_").lower()
        filename = Path(file_path).name.replace(" ", "_").lower()
        return f"backy_backups/{db_name}/{filename}"
