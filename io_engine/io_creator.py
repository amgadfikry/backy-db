# io_engine/io_creator.py
from logger.logger_manager import LoggerManager
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
import platform

load_dotenv()


class IOCreator:
    """
    A class to handle file creation and management.
    This class provides methods to create files with specific name and extension.
    """

    def __init__(self, backup_type: str, db_name: str):
        """
        Initialize the FileCreator with a specific backup type.
        Args:
            backup_type (str): The type of backup that this file creator will handle.
        """
        self.logger = LoggerManager.setup_logger("io_engine")
        if backup_type not in ["backy", "sql"]:
            self.logger.error(
                f"Invalid backup type: {backup_type}. Must be 'backy' or 'sql'."
            )
            raise ValueError("Invalid backup type. Must be 'backy' or 'sql'.")
        self.backup_type = backup_type
        self.db_name = db_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.processing_path = self._generate_main_backup_path()

    def create_file(self, feature_name: str) -> Path:
        """
        Create a file based on the backup type and feature name.
        This method will create either a SQL file or a Backy file based on the backup type.
        Args:
            feature_name (str): The name of the feature for which the file is created.
        Returns:
            Path: The path to the created file.
        """
        return self._create_file_helper(feature_name, self.backup_type)

    def _create_file_helper(self, feature_name: str, ext: str) -> Path:
        """
        Create a file with the specified extension.
        It will generate a file name based on the database name, feature name, and current timestamp.
        Args:
            feature_name (str): The name of the feature for which the file is created.
            ext (str): The file extension (e.g., 'sql', 'backy').
        Returns:
            Path: The path to the created file.
        """
        try:
            file_name = f"{self.db_name}_{feature_name}_{self.timestamp}_backup.{ext}"
            file_path = Path(self.processing_path) / file_name
            file_path.touch()
            self.logger.info(f"{ext.upper()} file created: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Error creating {ext.upper()} file: {e}")
            raise RuntimeError(f"Failed to create {ext.upper()} file") from e

    def _generate_main_backup_path(self) -> Path:
        """
        Generate and create a default backup path based on the system and user
        append it to the backup path.
        then ensure the path exists or create it if it does not.
        This function sets the environment variable `MAIN_BACKUP_PATH` to the generated path.
        Args:
            db_name (str): db_name to append to the backup path.
        Returns:
            Path: The default backup path.
        """
        system = platform.system()

        if system == "Windows":
            base = Path.home() / "AppData" / "Roaming"
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".local" / "share"

        backup_path = base / "backy" / f"{self.db_name}_{self.timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        os.environ["MAIN_BACKUP_PATH"] = str(backup_path)

        return backup_path
