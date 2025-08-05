# security/services/decryption_service.py
from logger.logger_manager import LoggerManager
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class DecryptionService:
    """
    A service class for handling decryption operations.
    It provides methods to decrypt bytes
    """

    def __init__(self):
        """
        Initialize the DecryptionService with a logger.
        """
        self.logger = LoggerManager.setup_logger("security")

    def decrypt_bytes(self, encrypted_blob: bytes, symmetric_key: bytes) -> bytes:
        """
        Decrypt the provided encrypted blob using the symmetric key.
        It uses AES-GCM for decryption with the first 12 bytes
        of the encrypted blob are the nonce.
        Args:
            encrypted_blob (bytes): The encrypted data to be decrypted.
            symmetric_key (bytes): The symmetric key to decrypt the data.
        Returns:
            bytes: The decrypted data.
        Raises:
            ValueError: If the encrypted blob or symmetric key is not provided.
            RuntimeError: If there is an error during the decryption operation.
        """
        if not encrypted_blob:
            self.logger.error("No encrypted blob provided for decryption")
            raise ValueError("No encrypted blob provided for decryption")
        if not symmetric_key:
            self.logger.error("No symmetric key provided for decryption")
            raise ValueError("No symmetric key provided for decryption")

        try:
            print(f"Using symmetric key: {symmetric_key.hex()}")
            nonce = encrypted_blob[:12]
            ciphertext = encrypted_blob[12:]
            aesgcm = AESGCM(symmetric_key)
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            self.logger.error(f"Error decrypting data: {e}")
            raise RuntimeError(f"Error decrypting data: {e}") from e
