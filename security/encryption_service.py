# security/encryption_service.py
from security.security_engine import SecurityEngine
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from pathlib import Path
import os


class EncryptionService(SecurityEngine):
    """
    A service class for handling encryption operations.
    Inherits from SecurityEngine to utilize its methods.
    """

    def encrypt_using_symmetric_key(self) -> bytes:
        """
        Encrypt a file using a random symmetrical key
        1. Generate a random symmetric key.
        2. Read the zip file from the processing path.
        3. Encrypt the file using AESGCM with the generated key.
        4. Save the encrypted file in the processing path with a .enc extension.
        5. Return the generated symmetric key.
        Raises:
            FileNotFoundError: If no zip file is found in the processing path.
        Returns:
            key (bytes): The generated symmetric key used for encryption.
        """
        # Get the compressed file from the processing path and ensure it exists
        compress_file = list(
            self.processing_path.glob(f"*.{self.compression_extension}")
        )
        if not compress_file:
            self.logger.error(
                f"No {self.compression_extension} file found in the processing path."
            )
            raise FileNotFoundError(
                f"No {self.compression_extension} file found in the processing path."
            )
        compress_file = compress_file[0]

        try:
            # Generate a random symmetric key, create an AESGCM instance, and create a nonce
            key = AESGCM.generate_key(bit_length=256)
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)

            # Read the compressed file and encrypt the file data using AESGCM and nonce
            with open(compress_file, "rb") as file:
                plaintext = file.read()
            encrypted_data = aesgcm.encrypt(nonce, plaintext, None)

            # Write the encrypted data to a new file with .enc extension and with the nonce prepended
            encrypted_file_path = (
                self.processing_path
                / f"{compress_file.stem}.{self.compression_extension}.enc"
            )
            with open(encrypted_file_path, "wb") as file:
                file.write(nonce + encrypted_data)

            # Clean up the original compressed file
            if compress_file.exists():
                compress_file.unlink()

            self.logger.info("File encrypted successfully and saved")
            return key

        except Exception as e:
            self.logger.error(f"Error during encryption data with symmetric key: {e}")
            raise RuntimeError("Failed to encrypt data with symmetric key") from e

    def encrypt_symmetric_key_with_public_key(self, symmetric_key: bytes) -> Path:
        """
        Encrypt the symmetric key using the public key.
        1. Load the public key.
        2. Encrypt the symmetric key using the public key.
        3. save the encrypted symmetric key in file in processing path.
        Args:
            symmetric_key (bytes): The symmetric key to encrypt.
        Returns:
            Path: path of the file containing the encrypted symmetric key.
        Raises:
            ValueError: If the public key is not loaded.
        """
        # Ensure the public key is loaded before encryption
        if not self.public_key:
            self.logger.error("Public key is not loaded.")
            raise ValueError("Public key is not loaded.")

        try:
            # Encrypt the symmetric key using the public key with OAEP padding
            encrypted_symmetric_key = self.public_key.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # Save the encrypted symmetric key to a file in the processing path with a version suffix
            encrypted_file_path = (
                self.processing_path / f"encryption_key_{self.version}.enc"
            )
            with open(encrypted_file_path, "wb") as file:
                file.write(encrypted_symmetric_key)

            self.logger.info("Symmetric key encrypted successfully and saved to file")
            return encrypted_file_path

        except Exception as e:
            self.logger.error(f"Error encrypting symmetric key with public key: {e}")
            raise RuntimeError("Failed to encrypt symmetric key with public key") from e
