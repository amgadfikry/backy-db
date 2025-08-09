# manager/backup_manager.py
from manager.manager_context import ManagerContext
from typing import Union
from pathlib import Path
from compression.compression_manager import CompressionManager
from storage.storage_manager import StorageManager
from io_engine.stream.write_stream import WriteStream


class BackupManager(ManagerContext):
    """
    The BackupManager class extends ManagerContext to manage backup operations.
    It utilizes the context's validation and IO creation capabilities.
    """

    def __init__(self, config: Union[str, Path, dict]) -> None:
        """
        Initialize the BackupManager with configuration.
        """
        super().__init__(config)
        self.define_config()
        self.create_main_directory()
        self.compressor = None
        self.encryptor = None
        self.integrator = None
        self.db_manager = None
        self.metadata = None
        self.call_services()

    def validate_config(self, config):
        """
        Validate the configuration by validator
        Args:
            config (Union[str, Path, dict]): The configuration for the backup.
        """
        self.validated_config = self.validator.validate_backup(config)

    def new_file_stream(self, feature: str, stream: object) -> object:
        """
        Create a new file for the given feature and open a write stream.
        Args:
            feature (str): The name of the feature for which the file is created.
            stream (object): The stream object to write data to.
        Returns:
            object: The opened write stream for the new file.
        """
        if self.backup_info["backup_type"] == "backy":
            return self._backy_file_stream(feature, stream)
        else:
            return self._sql_file_stream(feature, stream)

    def write_to_stream(self, stream: object, feature: str, statement: bytes) -> None:
        """
        Write the given statement to the provided stream.
        Args:
            stream (object): The write stream to write data to.
            feature (str): The name of the feature being processed.
            statement (bytes): The data to be written to the stream.
        """
        if self.backup_info["backup_type"] == "backy":
            self._write_to_backy(stream, feature, statement)
        else:
            self._write_to_sql(stream, statement)

    def close_stream(self, stream: object) -> None:
        """
        Close the provided stream.
        Args:
            stream (object): The stream to be closed.
        """
        if self.backup_info["backup_type"] == "backy":
            stream.close_stream()
        else:
            stream.close()

    def create_encryption_file(self) -> None:
        """
        Create an encryption file if encryption is enabled.
        It checks if the encryptor is enabled and retrieves the public key and key ID.
        If encryption is not enabled, it skips the creation of the encryption file.
        """
        if self.encryptor:
            public_key, key_id = self.encryptor.get_encrypted_key_and_key_id()
            self.io_creator.create_encryption_file(public_key, key_id)
            self.logger.info("encryption file is created successfully")
        else:
            self.logger.info(
                "encryption is not enabled, skipping encryption file creation"
            )

    def create_metadata(self) -> None:
        """
        Create metadata for the backup.
        It checks if the encryptor is enabled and retrieves the key ID.
        It then creates a metadata file with the database version and key ID.
        If the encryptor is not enabled, it sets the key ID to None.
        It also creates an instance of CreationMetadata to handle metadata creation.

        """
        if self.encryptor:
            _, key_id = self.encryptor.get_encrypted_key_and_key_id()
            self.encryptor.end_session()
            self.logger.info("security session is ended successfully")
        else:
            key_id = None

        version = self.db_manager.db.version

        self.metadata.create_metadata_file(version, key_id)
        self.logger.info("metadata file is created successfully")

    def create_integrity(self) -> None:
        """
        Create integrity checks for the backup.
        It checks if the integrity manager is enabled and creates integrity checks accordingly.
        """
        if self.integrator:
            self.integrator.create_integrity()
            self.logger.info("integrity checks are created successfully")
        else:
            self.logger.info(
                "integrity check is not enabled, skipping integrity creation"
            )

    def compress_and_upload(self) -> str:
        """
        Compress the folder and upload it to the storage.
        It uses the CompressionManager to compress the folder as a zip file
        and the StorageManager to upload the compressed file.
        """
        compressor = CompressionManager("zip")
        compressed_file = compressor.compress_folder(self.processing_path)
        self.logger.info("folder is compressed successfully")

        storage_manager = StorageManager(self.storage_config)
        file = storage_manager.upload(compressed_file)
        self.logger.info("compressed file is uploaded successfully")

        compressed_file.unlink(missing_ok=True)
        return file

    def _backy_file_stream(self, feature: str, stream: object) -> object:
        """
        It handle operations of creation of a new file for the given feature.
        It closes the previous stream if it exists and creates a new file.
        It returns the opened write stream for the new file.
        Args:
            feature (str): The name of the feature for which the file is created.
            stream (object): The stream object to write data to.
        Returns:
            object: The opened write stream for the new file.
        """
        if stream:
            stream.close_stream()
        file = self.io_creator.create_file(feature)
        new_stream = WriteStream(file)
        new_stream.open_stream()
        return new_stream

    def _sql_file_stream(self, feature: str, stream: object) -> object:
        """
        It handle operations of creation of a new file for the given feature.
        It closes the previous stream if it exists and creates a new file.
        It returns the opened write stream for the new file.
        Args:
            feature (str): The name of the feature for which the file is created.
            stream (object): The stream object to write data to.
        Returns:
            object: The opened write stream for the new file.
        """
        if stream:
            stream.close()
        file = self.io_creator.create_file(feature)
        new_stream = open(file, "w", encoding="utf-8")
        return new_stream

    def _write_to_backy(self, stream: object, feature: str, statement: bytes) -> None:
        """
        Write the given statement to the provided stream.
        It handles conversion, compression, and encryption if applicable.
        Args:
            stream (object): The write stream to write data to.
            feature (str): The name of the feature being processed.
            statement (bytes): The data to be written to the stream.
        """
        statement = self.converter.convert_str_to_bytes(statement)
        if self.compressor:
            statement = self.compressor.compress_bytes(statement)
        if self.encryptor:
            statement = self.encryptor.encrypt_bytes(statement)
        stream.write_stream(feature, statement)

    def _write_to_sql(self, stream: object, statement: str) -> None:
        """
        Write the given statement to the provided SQL stream.
        It handles normal write operations without compression or encryption.
        Args:
            stream (object): The write stream to write data to.
            statement (str): The SQL statement to be written to the stream.
        """
        if self.compressor:
            statement = self.compressor.compress_str(statement)
        if self.encryptor:
            statement = self.encryptor.encrypt_data(statement)
        stream.write(statement)
