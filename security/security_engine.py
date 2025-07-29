# security/security_engine.py
from dotenv import load_dotenv
from pathlib import Path
from typing import Tuple
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from logger.logger_manager import LoggerManager

load_dotenv()


class SecurityEngine:
    """
    Base class for security operations.
    This class initializes the security configuration and provides methods for
    handling private and public keys
    """

    def __init__(self, security_config: dict):
        self.logger = LoggerManager.setup_logger("security")
        # Get the password from the security configuration or raise an error if not provided
        self.password = security_config.get("private_key_password", None)
        self.private_key_size = security_config.get("private_key_size", "4096")
        self.integrity_password = security_config.get("integrity_password", None)
        self.integrity_check = security_config.get("integrity_check", False)
        self.compression_extension = security_config.get("compression_extension")

        # Get the processing path from environment variable and set the secret path in the parent directory
        env_path = os.getenv("MAIN_BACKUP_PATH", None)
        if not env_path:
            self.logger.error("MAIN_BACKUP_PATH environment variable is not set.")
            raise EnvironmentError("MAIN_BACKUP_PATH environment variable is not set.")
        self.processing_path = Path(env_path)
        self.secret_path = self.processing_path.parent / ".backy-secrets"

        # Ensure the secret path exists
        self.secret_path.mkdir(parents=True, exist_ok=True)

        # Check if there are public and private keys in the secret path and generate them if not
        if not self._check_keys_exist():
            self._generate_pub_and_priv_key()

        # Load the latest version of the public key and set the version
        self.public_key, self.version = self._load_public_key()

    def _check_keys_exist(self) -> bool:
        """
        Check if any version of the public and private keys exist in the secret path.
        Returns:
            bool: True if both keys exist, False otherwise.
        """
        # Get the list of public and private key files in the secret path
        private_key_path = list(self.secret_path.glob("private_key_*.pem"))
        public_key_path = list(self.secret_path.glob("public_key_*.pem"))

        # if no private or public key files exist, return False
        if not private_key_path or not public_key_path:
            self.logger.info("No public or private key files found in the secret path")
            return False

        self.logger.info("Public and private key files found in the secret path")
        return True

    def _generate_pub_and_priv_key(self, version: str = "v1") -> None:
        """
        Generate a public and private key pair for asymmetric encryption.
        1. Generate a new RSA private key.
        2. Derive the public key from the private key.
        3. Save the private key encrypted with the password in PEM format.
        4. Save the public key in PEM format.
        """
        try:
            # Generate a new RSA private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=int(self.private_key_size),
            )

            # Derive the public key from the private key
            public_key = private_key.public_key()

            # Save the private key and encrypt it using the password by using BestAvailableEncryption
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    self.password.encode()
                ),
            )

            # Save the private key to the secret path with the version in the filename
            with open(self.secret_path / f"private_key_{version}.pem", "wb") as f:
                f.write(private_key_bytes)

            # Convert the public key to PEM format
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # Save the public key to the secret path with the version in the filename
            with open(self.secret_path / f"public_key_{version}.pem", "wb") as f:
                f.write(public_key_bytes)
            self.logger.info(
                f"Public and private keys generated successfully with version {version}"
            )
        except Exception as e:
            self.logger.error(f"Error generating public and private keys: {e}")
            raise RuntimeError("Failed to generate public and private keys") from e

    def _load_public_key(self) -> Tuple[rsa.RSAPublicKey, str]:
        """
        Load the latest version of the public key from the secret path.
        Raises:
            FileNotFoundError: If no public key file is found.
        Returns:
            Tuple[rsa.RSAPublicKey, str]: The loaded public key and its version.
        """
        # Get the list of public key files in the secret path
        public_key_path = list(self.secret_path.glob("public_key_*.pem"))
        if not public_key_path:
            self.logger.error("No public key file found in the secret path.")
            raise FileNotFoundError("No public key file found in the secret path.")

        try:
            # Get the latest version of the public key by sorting the files
            latest_public_key = sorted(
                public_key_path, key=lambda x: x.stem.split("_")[-1], reverse=True
            )
            version = latest_public_key[0].stem.split("_")[-1]

            # Load the public key from the file
            with open(latest_public_key[0], "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            self.logger.info(
                f"Public key loaded successfully with the latest version: {version}"
            )
            return public_key, version

        except Exception as e:
            self.logger.error(f"Error loading public key: {e}")
            raise RuntimeError("Failed to load public key") from e
