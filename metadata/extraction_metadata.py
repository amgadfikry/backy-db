# metadata/extraction_metadata.py
from logger.logger_manager import LoggerManager
from pathlib import Path
import json
import os
from dotenv import load_dotenv

load_dotenv()


class ExtractionMetadata:
    """
    Class to extract data from the metadata file.
    It extract all info needed to restore the backup.
    it split extraction metadata into different methods according to the type of metadata.
    the user can call these methods to get the specific metadata they need.
    """

    def __init__(self):
        """
        Initialize the ExtractionMetadata class.
        Args:
            metadata_file (str): Path to the metadata file.
        """
        self.logger = LoggerManager.setup_logger("metadata")
        self.processing_path = os.getenv("MAIN_BACKUP_PATH")
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """
        Load metadata from the specified file.
        If the metadata file does not exist, it returns an empty dictionary and logs a warning.
        If the file is found, it reads the JSON content and returns it as a dictionary.
        If there is an error reading the file, it logs a warning and returns an empty dictionary.
        Returns:
            dict: The loaded metadata.
        """
        file = list(Path(self.processing_path).glob("*metadata.backy.json"))
        if not file:
            self.logger.warning("There is no metadata file at working directory")
            return {}

        try:
            with open(file[0], "r") as f:
                data = json.load(f)
                return data
        except Exception:
            self.logger.warning(f"Error reading metadata file {file[0]}")
            return {}

    def get_general_metadata(self) -> dict:
        """
        Extract general metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the general metadata.
        """
        return self.metadata.get("info", {})

    def get_backup_metadata(self) -> dict:
        """
        Extract backup metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the backup metadata.
        """
        return self.metadata.get("backup", {})

    def get_database_metadata(self) -> dict:
        """
        Extract database metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the database metadata.
        """
        return self.metadata.get("database", {})

    def get_compression_metadata(self) -> dict:
        """
        Extract compression metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the compression metadata.
        """
        return self.metadata.get("compression", {})

    def get_security_metadata(self) -> dict:
        """
        Extract security metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the security metadata.
        """
        return self.metadata.get("security", {})

    def get_integrity_metadata(self) -> dict:
        """
        Extract integrity metadata from the loaded metadata
        Returns:
            dict: A dictionary containing the integrity metadata.
        """
        return self.metadata.get("integrity", {})

    def get_storage_metadata(self) -> dict:
        """
        Extract storage metadata from the loaded metadata.
        This includes the storage type, object key, bucket name, and region.
        Returns:
            dict: A dictionary containing the storage metadata.
        """
        return self.metadata.get("storage", {})

    def get_full_metadata(self) -> dict:
        """
        Extract all metadata from the loaded metadata.
        Returns:
            dict: A dictionary containing all metadata.
        """
        return self.metadata
