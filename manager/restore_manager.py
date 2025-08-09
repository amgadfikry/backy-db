# manager/restore_manager.py
from manager.manager_context import ManagerContext
from typing import Union
from pathlib import Path
from storage.storage_manager import StorageManager
from compression.compression_manager import CompressionManager
from metadata.extraction_metadata import ExtractionMetadata
from config_schemas.validator import Validator
from io_engine.stream.read_stream import ReadStream


class RestoreManager(ManagerContext):
    """
    The RestoreManager class extends ManagerContext to manage restore operations.
    It utilizes the context's validation and IO creation capabilities.
    """

    def __init__(self, config: Union[str, Path, dict]) -> None:
        """
        Initialize the RestoreManager with configuration.
        """
        super().__init__(config)

    def validate_config(self, config):
        """
        Validate the configuration by validator
        Args:
            config (Union[str, Path, dict]): The configuration for the backup.
        """
        self.validated_config = self.validator.validate_restore(config)

    def download_and_extract(self) -> Path:
        """
        Download and extract the backup files.
        This method should handle the logic for downloading and extracting
        the backup files based on the provided configuration.
        """
        # Implementation of download and extraction logic goes here
        storage_config = self.validated_config["storage"]
        file_path = self.validated_config["backup_path"]
        storage_manager = StorageManager(storage_config)
        downloaded_file = storage_manager.download(file_path)

        compressor = CompressionManager("zip")
        extracted_files = compressor.decompress_folder(Path(downloaded_file))
        return extracted_files

    def align_metadata_with_config(self) -> None:
        """
        Align the metadata with the configuration.
        This method should ensure that the metadata is consistent with the
        current configuration and any changes made during the restore process.
        """
        self.metadata = ExtractionMetadata()
        metadata_dict = self.metadata.get_full_metadata()

        restore_features = self.validated_config["database"]["features"]
        backup_features = metadata_dict["database"]["features"]
        for feature, value in restore_features.items():
            if value and not backup_features[feature]:
                restore_features[feature] = False

        for key, value in self.validated_config["database"].items():
            metadata_dict["database"][key] = value

        validator = Validator()
        validator.validate_restore_metadata(metadata_dict)
        self.validated_config = metadata_dict

    def verify_integrity(self) -> None:
        """
        Verify the integrity of the backup files.
        This method should implement the logic to check the integrity of the
        restored files based on the configuration.
        """
        if self.integrator:
            self.integrator.verify_integrity()
            self.logger.info("Integrity check passed successfully")

    def arrange_files_for_restore(self) -> None:
        """
        Arrange the files for restore.
        This method should implement the logic to organize the files in the
        processing path for the restore operation.
        """
        # Implementation of file arrangement logic goes here
        # get all files in the processing path with specif backup type
        database_order = {
            "mysql": [
                "tables",
                "data",
                "views",
                "functions",
                "procedures",
                "triggers",
                "events",
            ]
        }
        backup_type = self.backup_info["backup_type"]
        db_type = self.database_config["db_type"]
        files = list(Path(self.processing_path).glob(f"*.{backup_type}"))

        if not files:
            self.logger.error("No files found for restore")
            raise RuntimeError("No files found for restore")

        if len(files) == 1:
            return [files[0]]

        # If multiple files, sort them by name  accoring to database restore order
        # And not add files that are not in features
        sorted_files = []
        features = self.database_config["features"]
        for order in database_order.get(db_type, []):
            for file in files:
                if order in file.name and features.get(order, False):
                    sorted_files.append(file)

        return sorted_files

    def read_file(self, file_path: Path, db: object) -> None:
        """
        Read the file and restore its content to the database.
        Args:
            file_path (Path): The path to the file to be read.
            db (object): The database manager instance to restore the data.
        """

        backup_type = self.backup_info["backup_type"]
        if backup_type == "sql":
            feature = str(file_path.name).split("_")[0]
            db.restore((feature, str(file_path)))
        else:
            read = ReadStream(file_path)
            read.open_stream()
            for feature, statement in read.read_stream():
                statement = self._parsing_statment(statement)
                db.restore((feature, statement))
            read.close_stream()

    def _parsing_statment(self, statement: str) -> str:
        """
        Parse the SQL statement
        to ensure it is in the correct format for restoration.
        This method handles decompression and decryption if necessary.
        It converts bytes to string if needed.
        All according to the metadata with the backup.
        Args:
            statement (str): The SQL statement to be parsed.
        Returns:
            Iterator[str]: An iterator over the parsed SQL statements.
        """
        if self.encryptor:
            statement = self.encryptor.decrypt_bytes(statement)
        if self.compressor:
            statement = self.compressor.decompress_bytes(statement)
        statement = self.converter.convert_bytes_to_str(statement)
        return statement
