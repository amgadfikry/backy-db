# database/database_metadata.py
from pathlib import Path
from typing import Dict
import json
from databases.database_base import DatabaseBase
from utils.generate_checksum import generate_sha256


class DatabaseMetadata(DatabaseBase):
    """
    Class to manage database metadata for the Backy project
    This class extends the DatabaseBase class and provides methods to handle
    metadata file, checksum generation, and create the main folder for backups.
    """
    def create_backup_folder(self, timestamp: str) -> Path:
        """
        Create a backup subfolder with the given timestamp and name of the database.
        to put all backups inside this subfolder then update the backup_folder_path.
        Args:
            timestamp (str): Timestamp for the backup folder.
        Returns:
            Path: Path to the created backup folder.
        """
        try:
            backup_folder = self.backup_folder_path / f"{self.db_name}_{timestamp}_backup"
            backup_folder.mkdir(parents=True, exist_ok=True)
            self.backup_folder_path = backup_folder
        except Exception as e:
            self.logger.error(f"Error creating backup folder: {e}")
            raise RuntimeError("Failed to create backup folder") from e

        self.logger.info(f"Backup folder created successfully at {self.backup_folder_path}")
        return self.backup_folder_path
    
    def create_metadata_file(self, timestamp: str) -> Path:
        """
        Create a metadata file for the backup, including database details and backup features.
        Args:
            timestamp (str): Timestamp for the metadata file.
        Returns:
            Path: Path to the created metadata file.
        """
        # Get all files in the backup folder
        backup_files = list(self.backup_folder_path.glob("*"))
        if not backup_files:
            self.logger.error("No backup files found to create metadata.")
            raise FileNotFoundError("No backup files found in the backup folder.")

        # Create metadata dictionary
        metadata: Dict = {
            "db_type": self.db_type,
            "version": self.version,
            "timestamp": timestamp,
            "db_name": self.db_name,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "backup_folder": self.backup_folder_path.name,
            "backup_files": [f.name for f in backup_files],
            "total_backup_size": sum(f.stat().st_size for f in backup_files),
            "number_of_files": len(backup_files),
            "features": {
                "tables": self.tables,
                "data": self.data,
                "views": self.views,
                "functions": self.functions,
                "procedures": self.procedures,
                "triggers": self.triggers,
                "events": self.events,
            }
        }

        # Create metadata file
        metadata_file = self.backup_folder_path / f"{self.db_name}_{timestamp}_metadata.json"
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error creating metadata file: {e}")
            raise RuntimeError("Failed to create metadata file") from e

        self.logger.info(f"Metadata file created successfully at {metadata_file}")
        return metadata_file
    
    def create_checksum_file(self, timestamp: str) -> Path:
        """
        Generate a SHA-256 checksum for all backup files in the backup folder.
        This checksum file will help verify the integrity of the backup files.
        Args:
            timestamp (str): Timestamp for the checksum file.
        Returns:
            Path: The path to the created checksum file.
        """
        # Get all files in the backup folder, sort them and ensure they are existent
        backup_files = sorted(self.backup_folder_path.glob("*"))
        if not backup_files:
            self.logger.error("No backup files found to generate checksums.")
            raise FileNotFoundError("No backup files found to generate checksums.")

        checksum_file = self.backup_folder_path / f"{self.db_name}_{timestamp}_checksum.sha256"

        # Generate checksums for each file
        try:
            with open(checksum_file, 'w', encoding='utf-8') as f:
                for file in backup_files:
                    checksum = generate_sha256(file)
                    f.write(f"{checksum}  {file.name}\n")
        except Exception as e:
            self.logger.error(f"Error creating checksum file: {e}")
            raise RuntimeError("Failed to create checksum file") from e

        self.logger.info(f"Checksum file created successfully at {checksum_file}")
        return checksum_file

    
