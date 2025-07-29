# security/security_manger.py
from security.security_engine import SecurityEngine
from security.encryption_service import EncryptionService
from security.decryption_service import DecryptionService
from security.security_metadata import SecurityMetadata
from pathlib import Path


class SecurityManager(SecurityEngine):
    """
    A composite class that combines security operations, encryption, decryption,
    and metadata handling.
    """

    def __init__(self, security_config: dict):
        super().__init__(security_config)
        self.config = security_config
        self.metadata_service = SecurityMetadata(self.config)

    def encryption(self) -> Path:
        """
        Perform the encryption process.
        1. Encrypt the file using a symmetric key.
        2. Encrypt the symmetric key using the public key.
        3. Create metadata for the encrypted files.
        4. Copy the public key to the processing path.
        5. Check the integrity-check if enabled add integrity check file
        Returns:
            Path: path of the the folder containing encrypted file, metadata, encryption key, and public key.
        """
        try:
            encryption_service = EncryptionService(self.config)
            symmetric_key = encryption_service.encrypt_using_symmetric_key()
            encryption_service.encrypt_symmetric_key_with_public_key(symmetric_key)
            self.metadata_service.create_metadata()
            self.metadata_service.copy_public_key()
            if self.integrity_check:
                self.metadata_service.create_integrity_file()
            print(
                f"Encryption completed, encrypted data and generated metadata, encryption key, and public key in: {self.processing_path}"
            )
            return self.processing_path
        except Exception as e:
            print(f"Encryption failed: {e}")
            raise e

    def decryption(self) -> Path:
        """
        Perform the decryption process.
        1. Decrypt the symmetric key using the private key.
        2. Decrypt the file using the symmetric key.
        3. Return the path of the decrypted file.
        Returns:
            Path: path of the decrypted file.
        """
        try:
            decryption_service = DecryptionService(self.config)
            if self.integrity_check:
                if not self.metadata_service.verify_integrity():
                    raise ValueError(
                        "Integrity check failed. The file may have been tampered with."
                    )
            symmetric_key = decryption_service.decrypt_symmetric_key()
            decrypted_data_path = decryption_service.decrypt_data(symmetric_key)
            print(
                f"Decryption completed, decrypted file available at: {decrypted_data_path}"
            )
            return decrypted_data_path
        except Exception as e:
            print(f"Decryption failed: {e}")
            raise e
