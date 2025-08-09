# manager/manager_context.py
from logger.logger_manager import LoggerManager
from config_schemas.validator import Validator
from io_engine.data_converter import DataConverter
from io_engine.io_creator import IOCreator
from typing import Union
from pathlib import Path
from compression.compression_manager import CompressionManager
from security.security_manager import SecurityManager
from integrity.integrity_manager import IntegrityManager
from databases.database_manager import DatabaseManager
from metadata.creation_metadata import CreationMetadata


class ManagerContext:
    """
    Initialize the BackyDB class with configuration and path.
    This class provides a context for managing backup operations,
    including validation, IO creation, and service management.
    It sets up the logger, validates the configuration, and initializes
    various managers for compression, encryption, integrity checks, and storage.
    It also defines the main directory for processing and calls the necessary services.
    It should be extended by specific managers like BackupManager.
    """

    def __init__(self, config: Union[str, Path, dict]) -> None:
        """
        Initialize the ManagerContext class with configuration and path.
        Args:
            config (Union[str, Path, dict]): The configuration for the backup or restore.
        """
        self.logger = LoggerManager.setup_logger("backy_db")
        self.validator = Validator()
        self.converter = DataConverter()
        self.processing_path = None
        self.io_creator = None
        self.compressor = None
        self.encryptor = None
        self.integrator = None
        self.db_manager = None
        self.validate_config(config)

    def validate_config(self, config: Union[str, Path, dict]) -> None:
        """
        Validate the configuration by validator
        Args:
            config (Union[str, Path, dict]): The configuration for the backup or restore.
        """
        raise NotImplementedError("This method should be implemented in subclasses")

    def create_main_directory(self, backup_type: str = None) -> None:
        """
        Create the main directory for processing.
        It initializes the IOCreator with the backup type and database name,
        and sets the processing path.
        """
        if backup_type is None:
            backup_type = self.backup_info["backup_type"]
        db_name = self.validated_config['database']['db_name']
        self.io_creator = IOCreator(backup_type, db_name)
        self.processing_path = self.io_creator.processing_path
        self.logger.info("Processing is created successfully at")

    def define_config(self) -> None:
        """
        Define the configuration for backup or restore.
        It extracts the backup, database, compression, security, integrity,
        and storage configurations from the validated configuration.
        This method should be called after the configuration is validated.
        It sets up the necessary configurations for the backup or restore process.
        """
        self.backup_info = self.validated_config["backup"]
        self.database_config = self.validated_config["database"]
        self.compression_config = self.validated_config["compression"]
        self.security_config = self.validated_config["security"]
        self.integrity_config = self.validated_config["integrity"]
        self.storage_config = self.validated_config["storage"]

    def call_services(self):
        """
        Call the services based on the configuration.
        This method should be implemented in subclasses to start the necessary services.
        It initializes the compression, encryption, integrity checks,
        and database manager based on the configuration.
        """
        if self.compression_config["compression"]:
            self.compressor = CompressionManager(
                self.compression_config["compression_type"]
            )

        if self.security_config["encryption"]:
            self.encryptor = SecurityManager(self.security_config)

        if self.integrity_config["integrity_check"]:
            self.integrator = IntegrityManager(self.integrity_config["integrity_type"])

        self.db_manager = DatabaseManager(self.database_config)

        self.metadata = CreationMetadata(self.validated_config)
