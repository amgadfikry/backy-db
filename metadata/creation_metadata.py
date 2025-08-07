# metadata/creation_metadata.py
from datetime import datetime
from logger.logger_manager import LoggerManager
import uuid
import platform
import os
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()


class CreationMetadata:
    """
    Class to generate metadata for the creation process of backups.
    This class provides methods to generate various types of metadata
    including general, backup, database, compression, security, integrity,
    and storage metadata.
    """

    def __init__(self, config):
        """
        Initialize the CreationMetadata class.
        Args:
            config (dict): Configuration dictionary containing settings for the backup process.
        """
        self.logger = LoggerManager.setup_logger("metadata")
        self.config = config
        self.processing_path = os.getenv("MAIN_BACKUP_PATH")
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def generate_general_metadata(self) -> dict:
        """
        Generate general metadata for the creation process.
        This includes information about the system, platform, and Python version.
        Returns:
            dict: A dictionary containing the general metadata.
        """
        info = {
            "creation_time": self.timestamp,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "system": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
        }
        return info

    def generate_backup_metadata(self) -> dict:
        """
        Generate metadata for the backup process.
        This includes information about the backup ID, creation time, total files,
        total size, and backup type.
        Returns:
            dict: A dictionary containing the backup metadata.
        """
        backup_data = self.config.get("backup", {})
        files = Path(self.processing_path).glob("*")
        file_list = [
            file
            for file in files
            if file.is_file() and (file.suffix == ".sql" or file.suffix == ".backy")
        ]
        total_size = sum(file.stat().st_size for file in file_list)

        backup = {
            "backup_id": str(uuid.uuid4()),
            "backup_time": self.timestamp,
            "total_files": len(file_list),
            "total_size": total_size,
            "files": [file.name for file in file_list],
            "backup_type": self.get_files_extension(),
            "backup_description": backup_data.get("backup_description", ""),
            "expiry_date": backup_data.get("expiry_date", None),
        }
        return backup

    def generate_database_metadata(self, version: str) -> dict:
        """
        Generate metadata for the database creation.
        This includes information about the database type, version,
        host, port, user, database name, multiple files, features,
        restore mode, and conflict mode.
        Args:
            version (str): The version of the database.
        Returns:
            dict: A dictionary containing the metadata.
        """
        database_data = self.config.get("database", {})
        database = {
            "database_type": database_data.get("database_type"),
            "database_version": version,
            "host": database_data.get("host"),
            "port": database_data.get("port"),
            "user": database_data.get("user"),
            "db_name": database_data.get("db_name"),
            "multiple_files": database_data.get("multiple_files"),
            "features": database_data.get("features"),
            "restore_mode": self.get_files_extension(),
            "conflict_mode": database_data.get("conflict_mode", "skip"),
        }
        return database

    def generate_compression_metadata(self) -> dict:
        """
        Generate metadata for the compression process.
        This includes information about the compression type, level, and method.
        Returns:
            dict: A dictionary containing the compression metadata.
        """
        compression_data = self.config.get("compression", {})
        compression = {
            "compression": compression_data.get("compression", "none"),
            "compression_level": compression_data.get("compression_level", 6),
            "compression_type": compression_data.get("compression_type"),
        }
        return compression

    def generate_security_metadata(self, key_id: str) -> dict:
        """
        Generate metadata for the security settings.
        This includes information about encryption, type, provider,
        key size, key version, and encryption file.
        Args:
            key_id (str): The unique identifier for the key.
        Returns:
            dict: A dictionary containing the security metadata.
        """
        security_data = self.config.get("security", {})
        security = {
            "encryption": security_data.get("encryption", False),
            "type": security_data.get("type", "keystore"),
            "provider": security_data.get("provider"),
            "key_size": security_data.get("key_size"),
            "key_version": key_id.split("_")[-1] if key_id else None,
            "encryption_file": f"{key_id}.enc" if key_id else None,
        }
        return security

    def generate_integrity_metadata(self) -> dict:
        """
        Generate metadata for the integrity checks.
        This includes information about the integrity check and type.
        Returns:
            dict: A dictionary containing the integrity metadata.
        """
        integrity_data = self.config.get("integrity", {})
        integrity = {
            "integrity_check": integrity_data.get("integrity_check"),
            "integrity_type": integrity_data.get("integrity_type"),
        }
        return integrity

    def generate_storage_metadata(self, object_key: str) -> dict:
        """
        Generate metadata for the storage settings.
        This includes information about the storage type, object key,
        bucket name, and region.
        Args:
            object_key (str): The key for the object in storage.
        Returns:
            dict: A dictionary containing the storage metadata.
        """
        storage_data = self.config.get("storage", {})
        storage_type = storage_data.get("storage_type")
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME") if storage_type == "aws" else None
        region = os.getenv("AWS_REGION") if storage_type == "aws" else None
        storage = {
            "storage_type": storage_type,
            "object_key": object_key,
            "bucket_name": bucket_name,
            "region": region,
        }
        return storage

    def generate_full_metadata(
        self, version: str, key_id: str, object_key: str
    ) -> dict:
        """
        Generate full metadata for the creation process.
        Args:
            version (str): The version of the database.
            key_id (str): The unique identifier for the key.
            object_key (str): The key for the object in storage.
        Returns:
            dict: A dictionary containing all metadata.
        """
        metadata = {
            "info": self.generate_general_metadata(),
            "backup": self.generate_backup_metadata(),
            "database": self.generate_database_metadata(version),
            "compression": self.generate_compression_metadata(),
            "security": self.generate_security_metadata(key_id),
            "integrity": self.generate_integrity_metadata(),
            "storage": self.generate_storage_metadata(object_key),
        }
        return metadata

    def create_metadata_file(self, version: str, key_id: str, object_key: str) -> str:
        """
        Create a metadata file with the generated metadata.
        Args:
            version (str): The version of the database.
            key_id (str): The unique identifier for the key.
            object_key (str): The key for the object in storage.
        Returns:
            str: The path to the created metadata file.
        """
        metadata = self.generate_full_metadata(version, key_id, object_key)
        db_name = self.config.get("database", {}).get("db_name")
        metadata_name = f"{db_name}_{self.timestamp}_metadata.backy.json"
        metadata_file_path = Path(self.processing_path) / metadata_name

        try:
            with open(metadata_file_path, "w") as f:
                json.dump(metadata, f, indent=4)
            self.logger.info(f"Metadata file created at {metadata_file_path}")
            return str(metadata_file_path)
        except Exception as e:
            self.logger.error(f"Failed to create metadata file: {e}")
            raise RuntimeError(f"Failed to create metadata file: {e}")

    def get_files_extension(self) -> str:
        """
        Get the file extension based on the configuration.
        Returns:
            str: The file extension for the backup files.
        """
        if self.config.get("compression"):
            return "backy"
        else:
            return "sql"
