# security/services/encryption_service.py
from logger.logger_manager import LoggerManager
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """
    A service class for handling encryption operations.
    It provides methods to encrypt bytes.
    """

    def __init__(self):
        """
        Initialize the EncryptionService with a logger.
        """
        self.logger = LoggerManager.setup_logger("security")

    def encrypt_bytes(self, data: bytes, symmetric_key: bytes) -> bytes:
        """
        Encrypt the provided data using the symmetric key.
        It uses AES-GCM for encryption with 12 bytes of nonce.
        Args:
            data (bytes): The data to be encrypted.
            symmetric_key (bytes): The symmetric key to encrypt the data.
        Returns:
            bytes: The encrypted data.
        Raises:
            ValueError: If the data or symmetric key is not provided.
            RuntimeError: If there is an error during the encryption operation.
        """
        if not data:
            self.logger.error("No data provided for encryption")
            raise ValueError("No data provided for encryption")
        if not symmetric_key:
            self.logger.error("No symmetric key provided for encryption")
            raise ValueError("No symmetric key provided for encryption")

        try:
            print(f"Encrypting data with symmetric key: {symmetric_key.hex()}")
            aesgcm = AESGCM(symmetric_key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            return nonce + ciphertext

        except Exception as e:
            self.logger.error(f"Error encrypting data: {e}")
            raise RuntimeError(f"Error encrypting data: {e}") from e
