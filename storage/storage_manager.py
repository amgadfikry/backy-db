# storage/storage_manager.py
from storage.local_storage import LocalStorage
from logger.logger_manager import LoggerManager
from storage.aws_storage import AWSStorage


class StorageManager:
    """
    StorageManager orchestrates the storage operations for the Backy project.
    It initializes the storage configuration and provides methods to upload,
    download, and delete files in the specified storage.
    """

    # Mapping of storage types to their respective classes
    STORAGES = {
        "local": LocalStorage,
        "aws": AWSStorage,
    }

    def __init__(self, config: dict):
        """
        Initialize the StorageManager with the given configuration.
        Args:
            config (dict): The configuration dictionary containing storage details.
        """
        self.logger = LoggerManager.setup_logger("storage")
        storage_type = config.get("storage_type", "local").lower()
        db_name = config.get("db_name", "backy_db")

        # Validate the storage type is supported
        if storage_type not in self.STORAGES:
            self.logger.error(f"Unsupported storage type: {storage_type}")
            raise ValueError(f"Unsupported storage type: {storage_type}")

        # Initialize the storage instance based on the type
        self.storage = self.STORAGES.get(storage_type)(db_name)

    def upload(self, file_path: str) -> str:
        """
        Upload method that delegates the upload operation to the storage instance.
        Args:
            file_path (str): The path to the file to be uploaded.
        Returns:
            str: The path to the uploaded file.
        """
        return self.storage.upload(file_path)

    def download(self, file_path: str) -> str:
        """
        Download method that delegates the download operation to the storage instance.
        Args:
            file_path (str): The path to the file to be downloaded.
        Returns:
            str: The path to the downloaded file.
        """
        return self.storage.download(file_path)

    def validate_credentials(self) -> bool:
        """
        Validate credentials that delegates the validation to the storage instance.
        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        return self.storage.validate_credentials()

    def delete(self, file_path: str) -> None:
        """
        Delete method that delegates the delete operation to the storage instance.
        Args:
            file_path (str): The path to the file to be deleted.
        Raises:
            RuntimeError: If the delete operation fails.
        """
        return self.storage.delete(file_path)
