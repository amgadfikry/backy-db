# security/key_store/key_store_manager.py
from security.key_store.google_key_store import GoogleKeyStore
from security.key_store.local_key_store import LocalKeyStore
from logger.logger_manager import LoggerManager


class KeyStoreManager:
    """
    KeyStoreManager is responsible for managing different key store implementations.
    It provides methods to save, load, delete, and validate keys in the configured key store.
    This class abstracts the underlying key store implementation, allowing for easy switching between different key store types.
    Supported key store types include Google Cloud Secret Manager and local file-based key store.
    """

    # Mapping of store types to their respective implementations
    STORE_MAPPING = {
        "google": GoogleKeyStore,
        "local": LocalKeyStore,
    }

    def __init__(self, store_type: str = "local"):
        """
        Initialize the KeyStoreManager with the provided configuration.
        Args:
            store_config (dict): Configuration settings for the key store.
        """
        self.logger = LoggerManager.setup_logger("security")
        if store_type not in self.STORE_MAPPING:
            self.logger.error(f"Unsupported key store type: {store_type}")
            raise ValueError(f"Unsupported key store type: {store_type}")
        self.key_store = self.STORE_MAPPING[store_type]()

    def save_key(self, key_id: str, key_data: bytes) -> None:
        """
        Save a key to the configured key store.
        Args:
            key_id (str): Unique identifier for the key.
            key_data (bytes): The key data to be stored.
        """
        return self.key_store.save_key(key_id, key_data)

    def load_key(self, key_id: str) -> bytes:
        """
        Load a key from the configured key store.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bytes: The key data associated with the given key_id.
        """
        return self.key_store.load_key(key_id)

    def delete_key(self, key_id: str) -> None:
        """
        Delete a key from the configured key store.
        Args:
            key_id (str): Unique identifier for the key.
        """
        return self.key_store.delete_key(key_id)

    def validate_key(self, key_id: str) -> bool:
        """
        Validate the existence of a key in the configured key store.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bool: True if the key exists, False otherwise.
        """
        return self.key_store.validate_key(key_id)
