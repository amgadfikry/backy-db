# security/security_manager.py
from logger.logger_manager import LoggerManager
from security.engine.security_engine import SecurityEngine
from security.services.encryption_service import EncryptionService
from security.services.decryption_service import DecryptionService
from typing import Tuple


class SecurityManager:
    """
    SecurityManager is responsible for managing the security operations
    such as encryption and decryption of data using the SecurityEngine.
    It provides a high-level interface to interact with the security engine.
    """

    def __init__(self, security_config: dict):
        """
        Initialize the SecurityManager with the provided security configuration.
        This loads the symmetric key, encrypted symmetric key, and key ID
        from the SecurityEngine.
        It also sets up the encryption and decryption services.
        Args:
            security_config (dict): Configuration settings for the security engine.
                - Contains type, provider, key_size, key_version, and encryption_file.
        """
        self.logger = LoggerManager.setup_logger("security_manager")
        self.security_config = security_config
        self.__symmetric_key = None
        self.encrypted_symmetric_key = None
        self.key_id = None
        self.encryptor = EncryptionService()
        self.decryptor = DecryptionService()
        self.load_keys()

    def load_keys(self):
        """
        Load the symmetric key, encrypted symmetric key, and key ID
        from the SecurityEngine based on the provided security configuration.
        This method initializes the SecurityEngine and retrieves the keys.
        """
        engine = SecurityEngine(self.security_config)
        symmetric_key, encrypted_key, key_id = engine.get_keys()
        self.__symmetric_key = symmetric_key
        self.encrypted_symmetric_key = encrypted_key
        self.key_id = key_id

    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        This a wrapper method to encrypt bytes using the symmetric key.
        It uses the EncryptionService to perform the encryption.
        Args:
            data (bytes): The data to be encrypted.
        Returns:
            bytes: The encrypted data.
        Raises:
            RuntimeError: If the symmetric key is not loaded or if there is an error during encryption
        """
        if not self.__symmetric_key:
            self.logger.error("Symmetric key not loaded. Call load_keys() first.")
            raise RuntimeError("Symmetric key not loaded. Call load_keys() first.")
        return self.encryptor.encrypt_bytes(data, self.__symmetric_key)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        This a wrapper method to decrypt bytes using the symmetric key.
        It uses the DecryptionService to perform the decryption.
        Args:
            encrypted_data (bytes): The encrypted data to be decrypted.
        Returns:
            bytes: The decrypted data.
        Raises:
            RuntimeError: If the symmetric key is not loaded or if there is an error during decryption.
        """
        if not self.__symmetric_key:
            self.logger.error("Symmetric key not loaded. Call load_keys() first.")
            raise RuntimeError("Symmetric key not loaded. Call load_keys() first.")
        return self.decryptor.decrypt_bytes(encrypted_data, self.__symmetric_key)

    def get_encrypted_key_and_key_id(self) -> Tuple[bytes, str]:
        """
        Expose method returns a tuple containing the encrypted symmetric key
        and the key ID.
        Returns:
            Tuple[bytes, str]: The encrypted symmetric key and key ID.
        """
        return self.encrypted_symmetric_key, self.key_id

    def end_session(self):
        """
        This method is called to end the session and clear sensitive data
        from memory. It sets the symmetric key and encrypted symmetric key to None.
        It is important to clear sensitive data to prevent memory leaks and
        potential security vulnerabilities.
        """
        if self.__symmetric_key:
            self.__symmetric_key = None
        self.encrypted_symmetric_key = None
