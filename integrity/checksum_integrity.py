# core/integrity/checksum_integrity.py
from pathlib import Path
from integrity.integrity_base import IntegrityBase
import hashlib


class ChecksumIntegrity(IntegrityBase):
    """
    Class to handle checksum operations for file integrity verification.
    This class provides methods to compute checksums for files and create integrity files.
    """

    def generate_sha256(self, path: Path) -> str:
        """
        Generate SHA-256 checksum for a file at the given path.
        Args:
            path (Path): The path to the file for which to generate the checksum.
        Returns:
            str: The SHA-256 checksum of the file.
        """
        # Ensure the file exists and is a file
        self.check_path(path)

        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating SHA-256 checksum for {path}: {e}")
            raise RuntimeError(f"Failed to generate checksum for {path}") from e

    def create_integrity(self) -> Path:
        """
        Generate a SHA-256 checksum for all backup files in the backup folder.
        This checksum file will help verify the integrity of the backup files.
        Returns:
            Path: The path to the created checksum file.
        """
        # Get all files in the backup folder, sort them and ensure they are existent
        files = self.get_files_from_processing_path()

        # Generate checksums for each file
        try:
            checksum_file = self.processing_path / "integrity.sha256"
            with open(checksum_file, "w", encoding="utf-8") as f:
                for file in files:
                    if file.name == checksum_file.name:
                        continue
                    checksum = self.generate_sha256(file)
                    f.write(f"{checksum}  {file.name}\n")
            self.logger.info(f"Checksum file created successfully at {checksum_file}")
            return checksum_file
        except Exception as e:
            self.logger.error(f"Error creating checksum file: {e}")
            raise RuntimeError("Failed to create checksum file") from e

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the backup files using the checksum file.
        This method will read the checksum file and compare it with the actual files.
        Returns:
            bool: True if all files match their checksums, False otherwise.
        """
        # check if the integrity file exists and is a file
        integrity_file = self.processing_path / "integrity.sha256"
        self.check_path(integrity_file)

        try:
            with open(integrity_file, "r", encoding="utf-8") as f:
                for line in f:
                    checksum, filename = line.strip().split("  ")
                    if filename == integrity_file.name:
                        continue
                    file_path = self.processing_path / filename
                    self.check_path(file_path)
                    actual_checksum = self.generate_sha256(file_path)
                    if actual_checksum != checksum:
                        self.logger.error(f"Checksum mismatch for {filename}")
                        raise ValueError(f"Checksum mismatch for {filename}")
            self.logger.info("All files verified successfully against checksums.")
            return True
        except Exception as e:
            if isinstance(e, FileNotFoundError) or isinstance(e, ValueError):
                return False
            self.logger.error(f"Error verifying checksum file: {e}")
            raise RuntimeError("Failed to verify checksum file") from e
