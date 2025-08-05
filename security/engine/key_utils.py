# security/engine/key_utils.py
import os
from pathlib import Path
from dotenv import load_dotenv
from logger.logger_manager import LoggerManager
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

load_dotenv()


class KeyUtils:
    """
    Utility class provide some utils for key management, such as encrypting and decrypting symmetric keys
    """

    def __init__(self):
        """Initialize the KeyUtils with a logger."""
        self.logger = LoggerManager.setup_logger("security")

    def encrypt_symmetric_key_with_public_key(
        self, symmetric_key: bytes, public_key: bytes
    ) -> bytes:
        """
        Encrypt the symmetric key using the public key with OAEP padding.
        Args:
            symmetric_key (bytes): The symmetric key to be encrypted.
            public_key (bytes): The public key to encrypt the symmetric key.
        Returns:
            bytes: The encrypted symmetric key.
        Raises:
            RuntimeError: If there is an error during the encryption operation.
        """
        try:
            # Load the public key from the provided bytes
            public_key_obj = serialization.load_pem_public_key(public_key)
            # Encrypt the symmetric key using the public key with OAEP padding
            encrypted_symmetric_key = public_key_obj.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return encrypted_symmetric_key
        except Exception as e:
            self.logger.error(f"Failed to encrypt the symmetric key: {e}")
            raise RuntimeError("Failed to encrypt the symmetric key") from e

    def decrypt_symmetric_key_with_private_key(
        self, private_key: bytes, symmetric_key: bytes
    ) -> bytes:
        """
        Decrypt the symmetric key using the private key with OAEP padding.
        Args:
            private_key (bytes): The private key to decrypt the symmetric key.
            symmetric_key (bytes): The encrypted symmetric key to be decrypted.
        Returns:
            bytes: The decrypted symmetric key.
        Raises:
            RuntimeError: If there is an error during the decryption operation.
        """
        try:
            password = os.getenv("PRIVATE_KEY_PASSWORD").strip()
            # Load the private key from the provided bytes and decrypt it using the password
            private_key_obj = serialization.load_pem_private_key(
                private_key, password=password.encode()
            )
            # Decrypt the symmetric key using the private key with OAEP padding
            decrypted_symmetric_key = private_key_obj.decrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted_symmetric_key
        except Exception as e:
            self.logger.error(f"Failed to decrypt the symmetric key: {e}")
            raise RuntimeError("Failed to decrypt the symmetric key") from e

    def read_encryption_file(self, file: Path) -> bytes | None:
        """
        Read the symmetric key from the encryption file.
        Returns:
            bytes: The symmetric key read from the file or None if the file does not exist.
        Raises:
            FileNotFoundError: If the encryption file does not exist.
            RuntimeError: If there is an error reading the file.
        """
        if not file or not Path(file).exists():
            self.logger.error(f"Encryption file {file} does not exist.")
            raise FileNotFoundError(f"Encryption file {file} does not exist.")
        try:
            # Read the symmetric key from the file
            with open(file, "rb") as file:
                symmetric_key = file.read()
            return symmetric_key
        except Exception as e:
            self.logger.error(f"Failed to read encryption file: {e}")
            raise RuntimeError("Failed to read encryption file") from e
