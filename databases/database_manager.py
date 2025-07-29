# databases/database_manager.py
from pathlib import Path
from databases.mysql_database import MySQLDatabase
from logger.logger_manager import LoggerManager
from databases.database_metadata import DatabaseMetadata
from datetime import datetime


class DatabaseManager:
    """
    Manages the database operations for the Backy project.
    This class is responsible for initializing and managing the database backup and restore processes.
    """

    DATABASES = {
        "mysql": MySQLDatabase,
    }

    def __init__(self, database_config: dict):
        """
        Initialize the DatabaseManager with a specific database configuration.
        args:
            database_config (dict): Configuration dictionary for the database.
        """
        self.logger = LoggerManager.get_logger("database")
        database_type = database_config.get("db_type").lower()
        if database_type not in self.DATABASES:
            self.logger.error(f"Unsupported database type: {database_type}")
            raise ValueError(f"Unsupported database type: {database_type}")
        self.db = self.DATABASES[database_type](database_config)
        self.metadata = DatabaseMetadata(database_config)

    def backup(self) -> Path:
        """
        orchestrates the backup process for the database.
        using database-specific backup methods and metadata creation.
        Returns:
            Path: The path to the created backup folder.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            # Start the backup process by creating a backup folder
            self.logger.info("Starting database backup process.")
            backup_folder = self.metadata.create_backup_folder(timestamp)
            self.logger.info(f"Backup folder created at: {backup_folder}")

            # Connect to the database and perform the backup
            self.db.connect()
            self.logger.info("Database connection established.")

            # Perform the backup to database
            backup_files = self.db.backup(timestamp)
            if not backup_files:
                self.logger.error(
                    "No backup files were created during the backup process."
                )
                raise RuntimeError("No backup files were created.")
            self.logger.info(f"Backup files created: {backup_files}")

            # Create metadata and checksum files
            metadata_file = self.metadata.create_metadata(timestamp)
            self.logger.info(f"Metadata file created at: {metadata_file}")
            checksum_file = self.metadata.create_checksum(timestamp)
            self.logger.info(f"Checksum file created at: {checksum_file}")

            # Close the database connection
            self.db.close()
            self.logger.info("Database connection closed.")

            # Return the path to the backup folder
            self.logger.info("Database backup process completed successfully.")
            return backup_folder
        except Exception as e:
            self.logger.error(f"Error during backup process: {e}")
            raise RuntimeError(f"Failed to perform backup: {e}")

    def restore(self, backup_file: Path):
        self.logger.error("Restore method is not implemented for this database type.")
        raise NotImplementedError(
            "Restore method is not implemented for this database type."
        )
