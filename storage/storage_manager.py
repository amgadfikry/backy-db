# storage/storage_manager.py
from storage.local_storage import LocalStorage
from logger.logger_manager import LoggerManager
from pathlib import Path



class StorageManager:
    """
    StorageManager orchestrates the storage operations for the Backy project.
    It initializes the storage configuration and provides methods to upload,
    download, and delete files in the specified storage.
    """
    STORAGES = {
        'local': LocalStorage,
    }
    
    def __init__(self, config: dict):
        """
        Initialize the StorageManager with the given configuration.
        Args:
            config (dict): The configuration dictionary containing storage details.
        """
        self.logger = LoggerManager.setup_logger("storage")
        storage_type = config.get('storage_type', 'local').lower()
        if storage_type not in self.STORAGES:
            self.logger.error(f"Unsupported storage type: {storage_type}")
            raise ValueError(f"Unsupported storage type: {storage_type}")
        self.storage = self.STORAGES.get(storage_type)(config)

    def upload(self) -> Path:
        """
        Upload a file to the storage.
        Returns:
            Path: The path to the uploaded file.
        """
        return self.storage.upload()

    def download(self) -> Path:
        """
        Download a file from the storage.
        Returns:
            Path: The path to the downloaded file.
        """
        return self.storage.download()