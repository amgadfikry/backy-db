# core_integrity/integrity_manager.py
from pathlib import Path
from integrity.hmac_integrity import HMACIntegrity
from integrity.checksum_integrity import ChecksumIntegrity
from logger.logger_manager import LoggerManager


class IntegrityManager:
    """
    This class provides methods to create and verify integrity files using specified integrity services.
    It supports multiple integrity types such as HMAC and checksum.
    It initializes the appropriate integrity service based on the type specified.
    """

    INTEGRITY_TYPES = {"hmac": HMACIntegrity, "checksum": ChecksumIntegrity}

    def __init__(self, integrity_type: str):
        """
        Initialize the IntegrityManager with the specified integrity type.
        Args:
            integrity_type (str): The type of integrity check to perform (e.g., "hmac", "checksum").
        """
        self.logger = LoggerManager.setup_logger("integrity_manager")
        if integrity_type not in self.INTEGRITY_TYPES:
            self.logger.error(f"Unsupported integrity type: {integrity_type}")
            raise ValueError(f"Unsupported integrity type: {integrity_type}")
        self.integrity_service = self.INTEGRITY_TYPES[integrity_type]()

    def create_integrity(self) -> Path:
        """
        Create an integrity file using the specified integrity service.
        Returns:
            Path: The path to the created integrity file.
        """
        return self.integrity_service.create_integrity()

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of files using the specified integrity service.
        Args:
            integrity_file (Path): The path to the integrity file to verify.
        Returns:
            bool: True if integrity is verified, False otherwise.
        """
        return self.integrity_service.verify_integrity()
