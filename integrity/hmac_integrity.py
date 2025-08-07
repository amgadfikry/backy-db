# core/integrity/hmac_integrity.py
from pathlib import Path
import hmac
import hashlib
from dotenv import load_dotenv
from integrity.integrity_base import IntegrityBase
import os
from hashlib import pbkdf2_hmac
import secrets

load_dotenv()


class HMACIntegrity(IntegrityBase):
    """
    Class to handle HMAC operations for file integrity verification.
    This class provides methods to compute HMAC for files and create integrity files.
    """

    def __init__(self):
        """
        Initialize the HMACService with necessary configurations.
        """
        super().__init__()
        self.integrity_password = os.getenv("INTEGRITY_PASSWORD")

    def derive_key(
        self, password: str, salt: bytes, iterations: int = 100_000, key_len: int = 32
    ) -> bytes:
        """
        Derive a cryptographic key from the given password and salt using PBKDF2.
        Args:
            password (str): The password to derive the key from.
            salt (bytes): The salt to use for key derivation.
            iterations (int): The number of iterations for PBKDF2.
            key_len (int): The length of the derived key in bytes.
        Returns:
            bytes: The derived key.
        Raises:
            ValueError: If the password is empty or salt is not provided.
        """
        try:
            return pbkdf2_hmac(
                "sha256", password.encode(), salt, iterations, dklen=key_len
            )
        except Exception as e:
            self.logger.error(f"Error deriving key: {e}")
            raise RuntimeError("Failed to derive key") from e

    def compute_hmac(self, file_path: Path, key: bytes) -> str:
        """
        Compute HMAC for a file using SHA256.
        Args:
            file_path (Path): The path to the file for which to compute the HMAC.
            key (bytes): The key to use for HMAC computation.
        Returns:
            str: The computed HMAC as a hexadecimal string.
        """
        # Ensure the file exists and is a file
        self.check_path(file_path)
        # Ensure the key is provided
        if not key:
            self.logger.error("HMAC key must be provided.")
            raise ValueError("HMAC key must be provided.")

        try:
            h = hmac.new(key, digestmod=hashlib.sha256)
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            self.logger.error(f"Error computing HMAC for {file_path}: {e}")
            raise RuntimeError(f"Failed to compute HMAC for {file_path}") from e

    def create_integrity(self) -> Path:
        """
        Create an integrity file for the all files in the processing path.

        Returns:
            Path: The path to the created integrity file.
        """
        # Get all files in the processing path and ensure they exist
        files = self.get_files_from_processing_path()

        try:
            # derive the key from the integrity password
            salt = secrets.token_bytes(16)
            derived_key = self.derive_key(self.integrity_password, salt)
            # Create the integrity file path
            integrity_file_path = self.processing_path / "integrity.hmac"
            # Write the checksums to the integrity file with name and checksum
            with open(integrity_file_path, "w", encoding="utf-8") as f:
                # Write the salt used for key derivation at the top of the file
                f.write(f"salt: {salt.hex()}\n")

                for file in files:
                    if file.name == "integrity.hmac":
                        continue
                    checksum = self.compute_hmac(file, derived_key)
                    f.write(f"{checksum}  {file.name}\n")

            self.logger.info("Integrity file created successfully")
            return integrity_file_path
        except Exception as e:
            self.logger.error(f"Error creating integrity file: {e}")
            raise RuntimeError("Failed to create integrity file") from e

    def verify_integrity(self, integrity_file: Path) -> bool:
        """
        Verify the integrity of the files in the processing path.
        This will compare the hmac in the integrity file with the actual files.
        Returns:
            bool: True if all files match their hmac, False otherwise.
        """
        # Get the integrity file and ensure it exists
        self.check_path(integrity_file)

        try:
            # Read the integrity file and verify checksums
            with open(integrity_file, "r", encoding="utf-8") as f:
                # Read the salt from the integrity file
                salt_line = f.readline().strip()

                if not salt_line.startswith("salt: "):
                    self.logger.error(
                        "Integrity file does not contain a valid salt line."
                    )
                    raise ValueError(
                        "Integrity file does not contain a valid salt line."
                    )

                salt = bytes.fromhex(salt_line.strip().split(": ")[1])
                derived_key = self.derive_key(self.integrity_password, salt)

                for line in f:
                    checksum, filename = line.strip().split()
                    # Skip the integrity file itself
                    if filename == "integrity.hmac":
                        continue

                    # Get the file path and ensure it exists
                    file_path = integrity_file.parent / filename
                    self.check_path(file_path)
                    # Compute HMAC for the file and compare with checksum
                    computed_checksum = self.compute_hmac(file_path, derived_key)
                    if not hmac.compare_digest(computed_checksum, checksum):
                        self.logger.error(f"Checksum mismatch for file {filename}")
                        raise ValueError(f"Checksum mismatch for file {filename}")
            self.logger.info("Integrity check passed for all files")
            return True

        except Exception as e:
            if isinstance(e, FileNotFoundError) or isinstance(e, ValueError):
                return False
            self.logger.error(f"Error verifying integrity: {e}")
            raise RuntimeError("Failed to verify integrity") from e
