# security/kms/kms_manager.py
from security.kms.aws_kms import AWSKMS
from logger.logger_manager import LoggerManager


class KMSManager:
    """
    KMSManager is a factory class that provides access to different KMS implementations.
    It currently supports AWS KMS as the only provider.
    This class initializes the appropriate KMS client based on the specified provider.
    It provides methods to generate keys, retrieve public keys, decrypt symmetric keys,
    validate keys, and delete keys.
    """

    # Mapping of KMS providers to their implementations
    KMS_CLIENT = {
        "aws": AWSKMS,
    }

    def __init__(self, kms_provider: str = "aws"):
        """
        Initialize the KMSManager with the specified KMS provider.
        and check if the provider is supported.
        Args:
            kms_provider (str): The KMS provider to use (default is "aws").
        Raises:
            ValueError: If the specified KMS provider is not supported.
        """
        self.logger = LoggerManager.setup_logger("security")
        if kms_provider not in self.KMS_CLIENT:
            self.logger.error(f"Unsupported KMS provider: {kms_provider}")
            raise ValueError(f"Unsupported KMS provider: {kms_provider}")
        self.kms_client = self.KMS_CLIENT[kms_provider]()

    def generate_key(self, alias_name: str) -> str:
        """
        Generate a new KMS key and return its alias name.
        Args:
            alias_name (str): Name for the key alias.
        Returns:
            str: Alias name for the generated key.
        """
        return self.kms_client.generate_key(alias_name)

    def get_public_key(self, key_id: str) -> bytes:
        """
        Retrieve the public key associated with the KMS key_id.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bytes: The public key associated with the given key_id.
        """
        return self.kms_client.get_public_key(key_id)

    def decrypt_symmetric_key(self, key_id: str, encrypted_key: bytes) -> bytes:
        """
        Decrypt the symmetric key using the KMS key_id.
        Args:
            key_id (str): Unique identifier for the key.
            encrypted_key (bytes): The encrypted symmetric key to be decrypted.
        Returns:
            bytes: The decrypted symmetric key.
        """
        return self.kms_client.decrypt_symmetric_key(key_id, encrypted_key)

    def validate_key(self, key_id: str) -> bool:
        """
        Validate the existence and usability of a KMS key.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bool: True if the key exists and is enabled, False otherwise.
        """
        return self.kms_client.validate_key(key_id)

    def delete_key(self, key_id: str) -> None:
        """
        Delete a KMS key by its key_id.
        Args:
            key_id (str): Unique identifier for the key to be deleted.
        Raises:
            RuntimeError: If the key cannot be deleted.
        """
        self.kms_client.delete_key(key_id)
