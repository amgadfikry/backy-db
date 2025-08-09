# manager/backy_db.py
from logger.logger_manager import LoggerManager
from manager.backup_manager import BackupManager
from manager.restore_manager import RestoreManager
from typing import Union
from pathlib import Path
from dotenv import load_dotenv
from utils.delete_folder import delete_folder

load_dotenv()


class BackyDB:
    """
    The orchestrator for managing the BackyDB operations.
    This class integrates the BackupManager and RestoreManager
    to provide a unified interface for backup and restore operations.
    It initializes the necessary components, validates configurations,
    and orchestrates the backup and restore processes.
    """

    def __init__(self):
        """
        Initialize the BackyDB class with configuration and path.
        """
        self.logger = LoggerManager.setup_logger("backy_db")

    def backup(self, config: Union[str, Path, dict]) -> str:
        """
        Create a backup using the configured components.
        It initializes the BackupManager, sets up the database manager,
        and orchestrates the backup process.
        Args:
            config (Union[str, Path, dict]): The configuration for the backup.
        Returns:
            str: The path to the created backup file.
        """
        try:
            # Step 1: Initialize BackupManager with the provided configuration
            backup_manager = BackupManager(config)

            # Step 2: Initialize the database manager
            current_feature = None
            stream = None

            with backup_manager.db_manager as db:

                # Step 3: Iterate through the database and write to the stream
                for feature, statement in db.backup():

                    # Step 4: Create a new file stream for each feature
                    if feature != current_feature or not current_feature:
                        current_feature = feature
                        stream = backup_manager.new_file_stream(feature, stream)

                    # Step 5: Write the statement to the stream
                    backup_manager.write_to_stream(stream, feature, statement)

            # Step 6: Close the stream after writing all data
            backup_manager.close_stream(stream)

            # Step 7: Create encryption file if encryption is enabled
            backup_manager.create_encryption_file()

            # Step 8: Create metadata for the backup
            backup_manager.create_metadata()

            # Step 9: Create integrity file if integrity checks are enabled
            backup_manager.create_integrity()

            # Step 10: Compress and upload the backup
            return backup_manager.compress_and_upload()

        except Exception as e:
            self.logger.error(f"Backup process failed: {e}")
            raise RuntimeError(f"Backup failed: {e}") from e

    def restore(self, config: Union[str, Path, dict]) -> None:
        """
        Restore a backup using the provided configuration and metadata.
        It initializes the RestoreManager, validates the configuration,
        and orchestrates the restore process.
        Args:
            config (Union[str, Path, dict]): The configuration for the restore.
        """
        try:
            # Step 1: Initialize RestoreManager with the provided configuration
            restore_manager = RestoreManager(config)

            # Step 2: Validate the configuration come from user
            restore_manager.create_main_directory(backup_type="restore")

            # Step 3: Download and extract the backup files into the processing path
            restore_manager.download_and_extract()

            # Step 4: Verify the integrity of the downloaded files
            restore_manager.verify_integrity()

            # Step 5: Align metadata with the configuration to complete the restore process
            # Also recheck it again
            restore_manager.align_metadata_with_config()

            # Step 6: Define the configuration for the restore process
            restore_manager.define_config()

            # Step 7: Call services to restore the database
            restore_manager.call_services()

            # Step 8: Arrange files for restoration according to feature and normal
            # sequence of restoration (specific for each database)
            files = restore_manager.arrange_files_for_restore()

            # Step 9: Start the database manager for restoration context
            with restore_manager.db_manager as db:
                for file_path in files:

                    # Step 10: Read the file and restore it to the database
                    restore_manager.read_file(file_path, db)

        except Exception as e:
            self.logger.error(f"Restore process failed: {e}")
            raise RuntimeError(f"Restore failed: {e}") from e
        finally:
            # Step 11: Clean up the processing path after restoration
            if restore_manager:
                delete_folder(Path(restore_manager.processing_path))
