# security/kms/kms_base.py
from abc import ABC, abstractmethod
from logger.logger_manager import LoggerManager


class KMSBase(ABC):
    """
    Abstract base class for KMS operations that defines the interface for key management services.
    This class provides the structure for implementing various KMS providers.
    It includes methods for generating keys, retrieving public keys, decrypting symmetric keys,
    validating keys, and deleting keys.
    Each method must be implemented by subclasses that provide specific KMS functionality.
    """

    def __init__(self):
        """
        Initialize the KMS base class with a logger.
        """
        self.logger = LoggerManager.setup_logger("security")

    @abstractmethod
    def generate_key(self, alias_name: str) -> str:
        """
        Generate a new KMS key and return its unique identifier.
        Args:
            alias_name (str): Name for the key alias.
        Returns:
            str: Unique identifier for the generated key.
        """
        self.logger.error("generate_key method not implemented.")
        raise NotImplementedError("generate_key method not implemented.")

    @abstractmethod
    def get_public_key(self, key_id: str) -> bytes:
        """
        Retrieve the public key associated with the KMS key_id.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bytes: The public key associated with the given key_id.
        """
        self.logger.error("get_public_key method not implemented.")
        raise NotImplementedError("get_public_key method not implemented.")

    @abstractmethod
    def decrypt_symmetric_key(self, key_id: str, encrypted_key: bytes) -> bytes:
        """
        Send the encrypted symmetric key to KMS and get the decrypted key.
        Args:
            key_id (str): Unique identifier for the key.
            encrypted_key (bytes): The encrypted symmetric key to be decrypted.
        Returns:
            bytes: The decrypted symmetric key.
        """
        self.logger.error("decrypt_symmetric_key method not implemented.")
        raise NotImplementedError("decrypt_symmetric_key method not implemented.")

    @abstractmethod
    def validate_key(self, key_id: str) -> bool:
        """
        Validate the existence and usability of a KMS key.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bool: True if the key exists and is enabled, False otherwise.
        """
        self.logger.error("validate_key method not implemented.")
        raise NotImplementedError("validate_key method not implemented.")

    @abstractmethod
    def delete_key(self, key_id: str) -> None:
        """
        Delete a KMS key by its unique identifier.
        Args:
            key_id (str): Unique identifier for the key to be deleted.
        Raises:
            RuntimeError: If the key deletion fails.
        """
        self.logger.error("delete_key method not implemented.")
        raise NotImplementedError("delete_key method not implemented.")
