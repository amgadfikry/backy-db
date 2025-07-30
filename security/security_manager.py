# security/security_manager.py
from security.encryption_service import EncryptionService
from security.decryption_service import DecryptionService
from security.security_metadata import SecurityMetadata
from logger.logger_manager import LoggerManager


class SecurityManager:
    """
    A composite class that combines security operations, encryption, decryption,
    and metadata handling.
    """

    def __init__(self, security_config: dict):
        """
        Initialize the SecurityManager with the provided security configuration.
        Args:
            security_config (dict): The security configuration dictionary.
        """
        self.logger = LoggerManager.setup_logger("security")
        self.config = security_config
        self.metadata_service = SecurityMetadata(self.config)

    def encryption(self) -> None:
        """
        Perform the encryption process.
        1. Encrypt the file using a symmetric key.
        2. Encrypt the symmetric key using the public key.
        3. Create metadata for the encrypted files.
        4. Copy the public key to the processing path.
        5. Check the integrity-check if enabled add integrity check file
        """
        try:
            encryption_service = EncryptionService(self.config)
            symmetric_key = encryption_service.encrypt_using_symmetric_key()
            encryption_service.encrypt_symmetric_key_with_public_key(symmetric_key)
            self.metadata_service.create_metadata()
            self.metadata_service.copy_public_key()
            if self.config.get("integrity_check", False):
                self.metadata_service.create_integrity_file()
            self.logger.info("Encryption completed successfully")
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise e

    def decryption(self) -> None:
        """
        Perform the decryption process.
        1. Decrypt the symmetric key using the private key.
        2. Decrypt the file using the symmetric key.
        3. Return the path of the decrypted file.
        """
        try:
            decryption_service = DecryptionService(self.config)
            if self.config.get("integrity_check", False):
                self.metadata_service.verify_integrity()
            symmetric_key = decryption_service.decrypt_symmetric_key()
            decrypted_data_path = decryption_service.decrypt_data(symmetric_key)
            self.logger.info(
                f"Decryption completed, decrypted file available at: {decrypted_data_path}"
            )
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise e
