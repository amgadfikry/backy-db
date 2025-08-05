# security/key_store/key_store_base.py
from abc import ABC, abstractmethod
from logger.logger_manager import LoggerManager


class KeyStoreBase(ABC):
    """
    Abstract base class for key store implementations.
    This class defines the interface for key store operations.
    """

    def __init__(self):
        """
        Initialize the key store with configuration settings.
        Args:
            store_config (dict): Configuration settings for the key store.
        """
        self.logger = LoggerManager.setup_logger("security")

    @abstractmethod
    def save_key(self, key_id: str, key_data: bytes) -> None:
        """
        Save a key to the key store.
        Args:
            key_id (str): Unique identifier for the key.
            key_data (bytes): The key data to be stored.
        """
        self.logger.error("save_key method not implemented.")
        raise NotImplementedError("save_key method not implemented.")

    @abstractmethod
    def load_key(self, key_id: str) -> bytes:
        """
        Load a key from the key store.
        Args:
            key_id (str): Unique identifier for the key to be loaded.
        Returns:
            bytes: The key data associated with the given key_id.
        """
        self.logger.error("load_key method not implemented.")
        raise NotImplementedError("load_key method not implemented.")

    @abstractmethod
    def delete_key(self, key_id: str) -> None:
        """
        Delete a key from the key store.
        Args:
            key_id (str): Unique identifier for the key to be deleted.
        """
        self.logger.error("delete_key method not implemented.")
        raise NotImplementedError("delete_key method not implemented.")

    @abstractmethod
    def validate_key(self, key_id: str) -> bool:
        """
        Validate the credentials of a key in the key store.
        Args:
            key_id (str): Unique identifier for the key to be validated.
        Returns:
            bool: True if the key exists, False otherwise.
        """
        self.logger.error("validate_key method not implemented.")
        raise NotImplementedError("validate_key method not implemented.")
