# security/key_store/google_key_store.py
from security.key_store.key_store_base import KeyStoreBase
from google.cloud import secretmanager
from google.api_core.exceptions import AlreadyExists, NotFound
import os
from dotenv import load_dotenv

load_dotenv()


class GoogleKeyStore(KeyStoreBase):
    """
    Google Cloud Secret Manager key store implementation.
    This class provides concrete implementations for different key store operations using Google Cloud Secret Manager.
    It allows saving, loading, deleting, and validating keys in the Google Cloud environment.
    """

    def __init__(self):
        """
        Initialize the Google key store with configuration settings.
        """
        super().__init__()
        self.project_id = os.getenv("GCP_PROJECT_ID", None)
        self.client = secretmanager.SecretManagerServiceClient()

    def save_key(self, key_id: str, key_data: bytes) -> None:
        """
        Save a key to the Google Cloud Secret Manager.
        This method creates a new secret if it does not exist yet with name of the project.
        Then add the new version if new key is provided.
        Args:
            key_id (str): Unique identifier for the key.
            key_data (bytes): The key data to be stored.
        Raises:
            AlreadyExists: If the secret already exists.
            RuntimeError: If there is an error during the save operation.
        """
        try:
            # Create the secret if it does not exist with the name of the project "backy_secret_key"
            self.client.create_secret(
                request={
                    "parent": f"projects/{self.project_id}",
                    "secret_id": "backy_secret_key",
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            self.logger.info("Secret backy_secret_key created in GCP Secret Manager.")
        except AlreadyExists:
            self.logger.debug(
                "Secret backy_secret_key already exists, adding new version."
            )
        except Exception as e:
            self.logger.error(f"Failed to create secret backy_secret_key in GCP: {e}")
            raise RuntimeError("Failed to create secret backy_secret_key in GCP") from e

        # Add new data as a new version of the secret
        try:
            self.client.add_secret_version(
                request={
                    "parent": f"projects/{self.project_id}/secrets/backy_secret_key",
                    "payload": {"data": key_data},
                }
            )
            self.logger.info("Key saved as new version in Secret Manager.")
        except Exception as e:
            self.logger.error(f"Failed to save key to GCP: {e}")
            raise RuntimeError(f"Failed to save key to GCP: {e}") from e

    def load_key(self, key_id: str) -> bytes:
        """
        Load a key from the Google Cloud Secret Manager.
        This method retrieves the key data associated with the given key_id according to the versioning scheme.
        Args:
            key_id (str): Unique identifier for the key to be loaded.
        Returns:
            bytes: The key data associated with the given key_id.
        Raises:
            FileNotFoundError: If the key does not exist.
            RuntimeError: If there is an error during the load operation."""
        try:
            secret_path = self._secret_path(key_id)
            response = self.client.access_secret_version(name=secret_path)
            self.logger.info(f"Key {key_id} loaded from GCP Secret Manager.")
            return response.payload.data
        except NotFound:
            self.logger.error(f"Key {key_id} not found in GCP Secret Manager.")
            raise FileNotFoundError(f"Key {key_id} not found in GCP Secret Manager.")
        except Exception as e:
            self.logger.error(f"Failed to load key {key_id}: {e}")
            raise RuntimeError(f"Failed to load key {key_id}: {e}") from e

    def delete_key(self, key_id: str) -> None:
        """
        Delete a key from the Google Cloud Secret Manager.
        This method marks the key as destroyed, making it unavailable for future use.
        Args:
            key_id (str): Unique identifier for the key to be deleted.
        Raises:
            FileNotFoundError: If the key does not exist.
            RuntimeError: If there is an error during the delete operation.
        """
        try:
            secret_path = self._secret_path(key_id)
            self.client.destroy_secret_version(name=secret_path)
            self.logger.info(f"Key {key_id} deleted from GCP Secret Manager.")
        except NotFound:
            self.logger.error(f"Key {key_id} not found in GCP Secret Manager.")
            raise FileNotFoundError(f"Key {key_id} not found in GCP Secret Manager.")
        except Exception as e:
            self.logger.error(f"Failed to delete key {key_id}: {e}")
            raise RuntimeError(f"Failed to delete key {key_id}: {e}") from e

    def validate_key(self, key_id: str) -> str | None:
        """
        Validate the credentials needed to access the key in Google Cloud Secret Manager.
        and check if the key exists.
        Args:
            key_id (str): Unique identifier for the key to be validated.
        Returns:
            str | None: The key identifier if the key exists, None otherwise.
        """
        # Check if the project ID is set
        if not self.project_id:
            self.logger.error("GCP_PROJECT_ID is not set in the environment variables.")
            return None
        try:
            # Check if the secret exists and is not destroyed
            secret_path = self._secret_path(key_id)
            response = self.client.get_secret_version(name=secret_path)
            if response and response.state.name == "DESTROYED":
                self.logger.warning(f"Key {key_id} is destroyed and cannot be used.")
                return None
            self.logger.info(f"Key {key_id} exists in GCP Secret Manager.")
            return f"backy_secret_key_{response.name.split('/')[-1]}"
        except NotFound:
            self.logger.error(f"Key {key_id} does not exist.")
            return None
        except Exception as e:
            self.logger.error(f"Failed to validate key {key_id}: {e}")
            return None

    def _secret_path(self, key_id: str) -> str:
        """
        Generate the full path to the secret in Google Cloud Secret Manager.
        This method constructs the path based on the project name and the key_id with versioning.
        If key_id is "auto", it returns the latest version.
        If key_id is in the format "backy_secret_key_{version}", it returns the specific version.
        Args:
            key_id (str): Unique identifier for the secret.(example: backy_secret_key_1
        Returns:
            str: Full path to the secret in the format 'projects/{project_id}/secrets/{key_id}'
        """
        base_path = f"projects/{self.project_id}/secrets/backy_secret_key/versions"
        if key_id == "auto":
            return f"{base_path}/latest"
        version = key_id.split("_")[-1]
        return f"{base_path}/{version}"
