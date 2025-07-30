# security/security_metadata.py
from pathlib import Path
import json
import shutil
from datetime import datetime
from security.security_engine import SecurityEngine
from utils.generate_hmac import compute_hmac


class SecurityMetadata(SecurityEngine):
    """
    A class for handling security metadata operations.
    Creating metadata files, copy public keys, and checking the integrity of files
    Inherits from SecurityEngine to utilize its methods.
    """

    def create_metadata(self) -> Path:
        """
        Create metadata file that will used all the information of the
        encryption, files, versions, and more.
        """
        # Data to be included in the metadata file
        metadata = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "main_folder": str(self.processing_path.name),
            "encrypted_data": f"{self.processing_path.name}.{self.compression_extension}.enc",
            "version": self.version,
            "HMAC": "SHA256",
            "Nonce": "12 bytes",
            "symmetric_key": "256 bits",
            "private_key_size": self.private_key_size,
            "encryption_type": "symmetric + asymmetric + password",
            "description": "This metadata file contains information about the encryption process.",
        }

        try:
            # Create the metadata file in the processing path
            metadata_file_path = self.processing_path / "security_metadata.json"
            with open(metadata_file_path, "w") as f:
                json.dump(metadata, f, indent=4)

            self.logger.info("Metadata file created successfully")
            return metadata_file_path

        except Exception as e:
            self.logger.error(f"Error creating metadata file: {e}")
            raise RuntimeError("Failed to create metadata file") from e

    def copy_public_key(self) -> Path:
        """
        Copy the public key to the processing path.
        Returns:
            Path: The path to the copied public key file.
        """
        # define the public key file name and pathbased on the version
        public_key_name = f"public_key_{self.version}.pem"
        public_key_path = self.secret_path / public_key_name

        # Check if the public key file exists
        if not public_key_path.exists():
            self.logger.error(
                f"Public key file {public_key_name} does not exist in the secret path."
            )
            raise FileNotFoundError(
                f"Public key file {public_key_name} does not exist in the secret path."
            )

        try:
            # Copy the public key file to the processing path
            shutil.copy2(public_key_path, self.processing_path)
            self.logger.info(
                f"Public key file {public_key_name} copied to the processing path"
            )
            return self.processing_path / public_key_name
        except Exception as e:
            self.logger.error(f"Error copying public key: {e}")
            raise RuntimeError("Failed to copy public key") from e

    def create_integrity_file(self) -> Path:
        """
        Create an integrity file for the all files in the processing path.
        This file will contain the SHA256 checksum of the file.
        Returns:
            Path: The path to the created integrity file.
        """
        # Get all files in the processing path and ensure they exist
        files = sorted(self.processing_path.glob("*"))
        if not files:
            self.logger.error("No files found in the processing path.")
            raise FileNotFoundError("No files found in the processing path.")

        try:
            # Create the integrity file path
            integrity_file_path = self.processing_path / "integrity.hmac"
            # Write the checksums to the integrity file with name and checksum
            with open(integrity_file_path, "w", encoding="utf-8") as f:
                for file in files:
                    if file.name == "integrity.hmac":
                        continue
                    checksum = compute_hmac(file, self.integrity_password.encode())
                    f.write(f"{checksum}  {file.name}\n")

            self.logger.info("Integrity file created successfully")
            return integrity_file_path
        except Exception as e:
            self.logger.error(f"Error creating integrity file: {e}")
            raise RuntimeError("Failed to create integrity file") from e

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the files in the processing path.
        This will compare the checksums in the integrity file with the actual files.
        Returns:
            bool: True if all files match their checksums, False otherwise.
        """
        # Get the integrity file and ensure it exists
        integrity_file_path = self.processing_path / "integrity.hmac"
        if not integrity_file_path.exists():
            self.logger.error("Integrity file does not exist in the processing path.")
            raise FileNotFoundError(
                "Integrity file does not exist in the processing path."
            )

        try:
            # Read the integrity file and verify checksums
            with open(integrity_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    checksum, filename = line.strip().split()
                    # Skip the integrity file itself
                    if filename == "integrity.hmac":
                        continue
                    # Get the file path and ensure it exists
                    file_path = self.processing_path / filename
                    if not file_path.exists():
                        self.logger.error(
                            f"File {filename} does not exist in the processing path."
                        )
                        raise FileNotFoundError(
                            f"File {filename} does not exist in the processing path."
                        )
                    # Compute HMAC for the file and compare with checksum
                    computed_checksum = compute_hmac(
                        file_path, self.integrity_password.encode()
                    )
                    if computed_checksum != checksum:
                        self.logger.error(f"Checksum mismatch for file {filename}")
                        raise ValueError(f"Checksum mismatch for file {filename}")
            self.logger.info("Integrity check passed for all files")
            return True

        except Exception as e:
            if isinstance(e, FileNotFoundError) or isinstance(e, ValueError):
                raise e
            self.logger.error(f"Error verifying integrity: {e}")
            raise RuntimeError("Failed to verify integrity") from e
