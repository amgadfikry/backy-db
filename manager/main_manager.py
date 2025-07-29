# manger/main_manager.py
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
from utils.delete_folder import delete_folder
from utils.generate_main_backup_path import generate_main_backup_path
from databases.database_manager import DatabaseManager
from compression.compression_manager import CompressionManager
from schema.backup_schema import BackupConfig
from logger.logger_manager import LoggerManager
from security.security_manager import SecurityManager
from storage.storage_manager import StorageManager

load_dotenv()


class MainManager:
    """
    MainManager orchestrates the backup process for the Backy project.
    It initializes the database and storage configurations, manages the backup creation,
    and handles the compression and Encryption of backup files.
    """
    LOGGER = LoggerManager.setup_logger("manager")

    @staticmethod
    def create_backup(config: dict) -> None:
        """
        Create the backup through these steps:
        1. Create a working directory where all the operations will be occring.
        2. Initialize the database manager to handle database operations.
        3. Initialize the compression manager to handle compression operations.
        4. Initialize the encryption manager to handle encryption operations.
        3. Initialize the storage manager to handle storage operations.
        Args:
            config (dict): The configuration dictionary containing all configration details
        Returns:
            None
        """
        try:
            # step 1: Validate the configuration by pydantic then dump it to dictionary
            validated_config = BackupConfig(**config)
            config_dict = validated_config.model_dump()

            # step 2: split the configuration into, database, compression, encryption, and storage
            database_config = config_dict.get("database")
            compression_config = config_dict.get("compression")
            security_config = config_dict.get("security")
            storage_config = config_dict.get("storage")

            # step 3: Create a working directory for the backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            database_name = database_config.get("db_name")
            generate_main_backup_path(subfolder=f"{database_name}_{timestamp}")
            MainManager.LOGGER.info(f"Working directory created successfully")

            # step 4: Initialize the database manager and perform the backup
            db_manager = DatabaseManager(database_config)
            db_manager.backup()
            MainManager.LOGGER.info(f"Backup folder created successfully")

            # step 5: Initialize the compression manager and compress the backup folder
            if compression_config.get("compression"):
                compression_manager = CompressionManager(compression_config)
                compression_manager.compress()
                MainManager.LOGGER.info(f"Backup compressed successfully")

            # step 6: Initialize the encryption manager and encrypt the compressed file
            if security_config.get("encryption"):
                encryption_manager = SecurityManager(security_config)
                encryption_manager.encrypt()
                MainManager.LOGGER.info(f"Backup encrypted successfully")

            # step 7: Initialize the storage manager and store the backup
            storage_manager = StorageManager(storage_config)
            storage_manager.upload()
            MainManager.LOGGER.info("Backup stored in the specified storage location")

        except Exception as e:
            MainManager.LOGGER.error(f"An error occurred during the backup process: {e}")
            raise RuntimeError(f"Backup process failed") from e
        
        finally:
            working_dir = Path(os.environ.get("MAIN_BACKUP_PATH", ""))
            if working_dir.exists():
                delete_folder(working_dir)
                MainManager.LOGGER.info("Working directory deleted successfully")
            else:
                MainManager.LOGGER.warning("Working directory does not exist, nothing to delete")
