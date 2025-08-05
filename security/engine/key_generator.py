# security/engine/key_generator.py
from dotenv import load_dotenv
from logger.logger_manager import LoggerManager
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


load_dotenv()


class KeyGenerator:
    """
    A class to generate cryptographic keys.
    This class provides methods to generate secure keys for encryption and decryption.
    It will generate the symmetric key and the public/private key pair.
    """

    def __init__(self):
        """
        Initialize the KeyGenerator with a logger.
        """
        self.logger = LoggerManager.setup_logger("security")

    def generate_symmetric_key(self, bit_length=256) -> bytes:
        """
        Generate a random symmetric key.
        Args:
            bit_length (int): The length of the key in bits. Default is 256.
        Raises:
            RuntimeError: If the key generation fails.
        Returns:
            bytes: A random symmetric key.
        """
        try:
            return AESGCM.generate_key(bit_length=bit_length)
        except Exception as e:
            self.logger.error(f"Error generating symmetric key: {e}")
            raise RuntimeError("Failed to generate symmetric key") from e

    def generate_rsa_private_key(self, key_size=2048) -> bytes:
        """
        Generate a private key for asymmetric encryption.
        with the specified key size.
        And encrypt it with the private key password.
        Raises:
            RuntimeError: If the key generation fails.
        Args:
            key_size (int): The size of the key in bits. Default is 2048.
        Returns:
            PrivateKey: A private key byte string.
        """
        try:
            # Generate a new RSA private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=int(key_size),
            )

            # Save the private key as a PEM bytes and encrypt it using the password by using BestAvailableEncryption
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    os.getenv("PRIVATE_KEY_PASSWORD").strip().encode()
                ),
            )

            return private_key_bytes
        except Exception as e:
            self.logger.error(f"Error generating RSA private key: {e}")
            raise RuntimeError("Failed to generate RSA private key") from e

    def extract_public_key(self, private_key: bytes) -> bytes:
        """
        Extract the public key from the given private key.
        Args:
            private_key (bytes): The private key in PEM format.
        Returns:
            bytes: The public key in PEM format.
        Raises:
            ValueError: If the private key is invalid.
            RuntimeError: If the public key extraction fails.
        """
        # Validate the private key input
        if not private_key:
            self.logger.error("Private key must be provided to extract the public key.")
            raise ValueError("Private key must be provided to extract the public key.")

        try:
            # Load the private key object from the PEM bytes and decrypt it using the password
            password = os.getenv("PRIVATE_KEY_PASSWORD").strip()
            private_key_obj = serialization.load_pem_private_key(
                private_key, password=password.encode()
            )

            # Extract the public key from the private key object
            public_key = private_key_obj.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            return public_key_bytes
        except Exception as e:
            self.logger.error(f"Error extracting public key: {e}")
            raise RuntimeError("Error extracting public key") from e
