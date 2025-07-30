# security/decryption_service.py
from security.security_engine import SecurityEngine
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes
import json
from pathlib import Path


class DecryptionService(SecurityEngine):
    """
    A service class for handling decryption operations.
    Inherits from SecurityEngine to utilize its methods.
    """

    def _decrypt_private_key(self, version: str = "v1") -> rsa.RSAPrivateKey:
        """
        Decrypt the private key using the password.
        1. Load the private key from the secret path.
        2. Decrypt the private key using the password.
        Args:
            version (str): The version of the private key to load.
        Returns:
            rsa.RSAPrivateKey: The decrypted private key.
        """
        # Load the private key from the secret path and ensure it exists
        private_key_path = self.secret_path / f"private_key_{version}.pem"
        if not private_key_path.exists():
            self.logger.error("Private key file does not exist.")
            raise FileNotFoundError("Private key file does not exist.")
        try:
            # Load the private key from the file and decrypt it using the password
            with open(private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=self.password.encode()
                )

            self.logger.info("Private key loaded successfully")
            return private_key
        except Exception as e:
            self.logger.error(f"Error loading private key: {e}")
            raise RuntimeError("Failed to load private key") from e

    def decrypt_symmetric_key(self) -> bytes:
        """
        Decrypt the symmetric key using the private key.
        1. Load the private key.
        2. Decrypt the symmetric key using the private key.
        Returns:
            bytes: The decrypted symmetric key.
        Raises:
            ValueError: If the private key is not loaded.
        """
        # Get the metadata file and the encrypted symmetric key file
        metadata_file = self.processing_path / "metadata.json"
        encrypted_key_path = list(self.processing_path.glob("encryption_key_*.enc"))

        # Ensure the encrypted key file exists
        if not encrypted_key_path:
            self.logger.error("Encrypted symmetric key file does not exist.")
            raise FileNotFoundError("Encrypted symmetric key file does not exist.")

        try:
            # Load the metadata to get the version of the private key if metadata exists
            version = None
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                version = metadata.get("version", None)
            else:
                self.logger.warning("Metadata file does not exist")
            # If version is not specified, use the first encrypted key file's version
            if not version:
                version = encrypted_key_path[0].stem.split("_")[-1]

            # Decrypt the private key using the version and check if it loaded successfully
            private_key = self._decrypt_private_key(version)
            if not private_key:
                self.logger.error("Private key is not loaded.")
                raise ValueError("Private key is not loaded.")

            # Read the encrypted symmetric key
            with open(encrypted_key_path[0], "rb") as f:
                encrypted_key = f.read()

            # Decrypt the symmetric key using the private key with OAEP padding
            decrypted_symmetric_key = private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            self.logger.info("Symmetric key decrypted successfully.")
            return decrypted_symmetric_key

        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            self.logger.error(f"Error decrypting symmetric key: {e}")
            raise RuntimeError("Failed to decrypt symmetric key") from e

    def decrypt_data(self, symmetric_key: bytes) -> Path:
        """
        Decrypt a file using the symmetric key.
        1. Load the encrypted file.
        2. Decrypt the file contents using the symmetric key.
        Args:
            symmetric_key (bytes): The symmetric key to use for decryption.
        Returns:
            Path: The path to the decrypted file.
        """
        # Ensure the encrypted file exists in the processing path
        encrypted_data_path = list(
            self.processing_path.glob(f"*.{self.compression_extension}.enc")
        )
        if not encrypted_data_path:
            self.logger.error("No encrypted file found in the processing path.")
            raise FileNotFoundError("No encrypted file found in the processing path.")
        encrypted_data_path = encrypted_data_path[0]
        if not symmetric_key:
            self.logger.error("Symmetric key is not provided for decryption.")
            raise ValueError("Symmetric key is not provided for decryption.")

        try:
            # Load the encrypted data from the file
            with open(encrypted_data_path, "rb") as f:
                encrypted_data = f.read()

            # Decrypt the data using AESGCM with the symmetric key
            decrypted_data = AESGCM(symmetric_key).decrypt(
                nonce=encrypted_data[:12],
                data=encrypted_data[12:],
                associated_data=None,
            )

            # Write the decrypted data to a new file with the same name as the encrypted file but without the .enc extension
            decrypted_data_path = self.processing_path / f"{encrypted_data_path.stem}"
            with open(decrypted_data_path, "wb") as f:
                f.write(decrypted_data)

            # Remove the encrypted file after decryption
            if encrypted_data_path.exists():
                encrypted_data_path.unlink()

            self.logger.info(
                f"Data decrypted successfully and saved to {decrypted_data_path}"
            )
            return decrypted_data_path

        except Exception as e:
            self.logger.error(f"Error decrypting data: {e}")
            raise RuntimeError("Failed to decrypt data") from e
