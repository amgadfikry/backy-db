# security/key_store/local_key_store.py
from security.key_store.key_store_base import KeyStoreBase
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


class LocalKeyStore(KeyStoreBase):
    """
    Local key store implementation that stores keys in a local file system.
    This class provides concrete implementations for the abstract methods defined in KeyStoreBase.
    """

    def __init__(self):
        """
        Initialize the local key store with configuration settings.
        """
        super().__init__()
        self.store_path = os.getenv("LOCAL_KEY_STORE_PATH", None)

    def save_key(self, key_id: str, key_data: bytes) -> None:
        """
        Save a key to the local key store as a file.
        This method creates a new file with the key_id as the filename and writes the key_data to it.
        Args:
            key_id (str): Unique identifier for the key.
            key_data (bytes): The key data to be stored.
        Raises:
            RuntimeError: If there is an error during the save operation.
        """
        try:
            key_path = self._get_key_path(key_id)
            with open(key_path, "wb") as key_file:
                key_file.write(key_data)
            self.logger.info(f"Key {key_id} saved successfully to local store.")
        except Exception as e:
            self.logger.error(f"Failed to save key to local store: {e}")
            raise RuntimeError("Failed to save key to local store") from e

    def load_key(self, key_id: str) -> bytes:
        """
        Load a key from the local key store.
        This method reads the key data from a file with the name of the key_id.
        Args:
            key_id (str): Unique identifier for the key to be loaded.
        Returns:
            bytes: The key data associated with the given key_id.
        Raises:
            FileNotFoundError: If the key file does not exist.
        """
        try:
            key_path = self._get_key_path(key_id)
            with open(key_path, "rb") as key_file:
                key_data = key_file.read()
            self.logger.info(f"Key {key_id} loaded successfully from local store.")
            return key_data
        except FileNotFoundError as e:
            self.logger.error(f"Key {key_id} not found in local store.")
            raise FileNotFoundError(f"Key {key_id} not found in local store.") from e

    def delete_key(self, key_id: str) -> None:
        """
        Delete a key from the local key store.
        This method removes the file associated with the key_id from the local file system.
        Args:
            key_id (str): Unique identifier for the key to be deleted.
        Raises:
            FileNotFoundError: If the key file does not exist.
        """
        try:
            key_path = self._get_key_path(key_id)
            key_path.unlink()
            self.logger.info(f"Key {key_id} deleted successfully.")
        except FileNotFoundError as e:
            self.logger.error(f"Key {key_id} not found in local store.")
            raise FileNotFoundError(f"Key {key_id} not found in local store.") from e

    def validate_key(self, key_id: str) -> str | None:
        """
        Validate all credentials in the local key store.
        This method checks if the key store path exists, is a directory, and is writable.
        It also checks if the specified key exists in the local key store.
        Args:
            key_id (str): Unique identifier for the key to be validated.
        Returns:
            bool: True if the key exists, False otherwise.
        """
        if not self.store_path:
            self.logger.error(
                "Key store path is not set (LOCAL_KEY_STORE_PATH missing)."
            )
            return None

        store_path = Path(self.store_path)
        if not store_path.exists():
            self.logger.error(f"Key store path {self.store_path} does not exist.")
            return None

        if not store_path.is_dir():
            self.logger.error(f"Key store path {self.store_path} is not a directory.")
            return None

        if not os.access(store_path, os.W_OK):
            self.logger.error(f"Key store path {self.store_path} is not writable.")
            return None

        key_path = self._get_key_path(key_id)
        if not key_path or not key_path.exists():
            self.logger.error(f"Key {key_id} does not exist in local store.")
            return None

        return str(key_path.stem.split("/")[-1])  # Return the key ID without the path

    def _get_key_path(self, key_id: str) -> Path | None:
        """
        Get the full path to the key file based on the key_id.
        If key_id is "auto", it returns the latest key file based on naming convention with "backy_*" and versioning.
        If key_id is not existent, it raises a FileNotFoundError.
        Else, it returns the path to the key file with the name "{key_id}.pem".
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            Path: Full path to the key file.
        Raises:
            FileNotFoundError: If no key files are found when key_id is "auto".
        """
        store_path = Path(self.store_path)

        if key_id == "auto":
            files = list(store_path.glob("backy_*"))
            if not files:
                self.logger.warning("No key files found in local key store.")
                return None
            latest_key = sorted(
                files, key=lambda x: x.stem.split("_")[-1], reverse=True
            )
            return latest_key[0]

        store_path.mkdir(parents=True, exist_ok=True)
        return store_path / f"{key_id}.pem"
