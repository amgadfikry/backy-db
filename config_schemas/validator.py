# config_schemas/validator.py
from logger.logger_manager import LoggerManager
from config_schemas.schemas.backup_schema import BackupSchema
from config_schemas.schemas.restore_schema import RestoreSchema
from typing import Union
from pathlib import Path
import yaml
import json
from pydantic import ValidationError
import os
from dotenv import load_dotenv

load_dotenv()


class Validator:
    """
    Class to validate configuration schemas.
    This class provides methods to the schema either dict, yaml, or json format.
    It uses Pydantic models to ensure the configuration adheres to the defined schema.
    It also validate the environmental variables exist according to the schema.
    """

    SCHEMAS = {
        "backup": BackupSchema,
        "restore": RestoreSchema,
    }

    def __init__(self):
        """
        Initialize the Validator with predefined schemas.
        """
        self.logger = LoggerManager.setup_logger("validator")

    def validate_backup(self, config: Union[str, Path, dict]) -> dict:
        """
        Validate backup configuration.
        Args:
            config (Union[str, dict]): File path or dict to validate.
        Returns:
            dict: Validated configuration data.
        """
        config_data = self._validate_according_type(config, "backup")
        self._validate_environmental_variables(config_data)
        return config_data

    def validate_restore(self, config: Union[str, Path, dict]) -> dict:
        """
        Validate restore configuration.
        Args:
            config (Union[str, dict]): File path or dict to validate.
        Returns:
            dict: Validated configuration data.
        """
        config_data = self._validate_according_type(config, "restore")
        self._validate_environmental_variables(config_data)
        return config_data
    
    def validate_restore_metadata(self, config: dict) -> None:
        """
        Validate restore metadata configuration.
        This method checks for the presence of all required environmental variables
        that are needed for restore operations.
        Args:
            config (dict): Configuration data to validate.
        """
        self._validate_environmental_variables(config)

    def _load_config_from_file(self, file_path: Path) -> dict:
        """
        Load configuration from a file.
        If the file is in YAML or JSON format, it will parse the content.
        If the file format is unsupported, it raises a ValueError.
        Args:
            file_path (Path): Path to the configuration file.
        Returns:
            dict: Parsed configuration data.
        Raises:
            ValueError: If the file format is unsupported.
        """
        if file_path.suffix in [".yaml", ".yml"]:
            with file_path.open("r") as f:
                return yaml.safe_load(f)
        elif file_path.suffix == ".json":
            with file_path.open("r") as f:
                return json.load(f)
        else:
            self.logger.error(f"Unsupported file format: {file_path.suffix}")
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _validate_according_type(
        self, config: Union[str, Path, dict], schema_name: str
    ) -> dict:
        """
        Validate the config against the schema specified by schema_name.
        If the config is a file path, it will load the file and validate its content.
        If the config is a dict, it will validate it directly.
        Then return the validated configuration data as a dict.
        Args:
            config (Union[str, dict]): Config dict or file path.
            schema_name (str): Schema key.
        Returns:
            dict: Validated configuration data.
        Raises:
            FileNotFoundError: If the config file does not exist.
            ValidationError: If the config does not match the schema.
        """
        schema = self.SCHEMAS.get(schema_name)
        if isinstance(config, dict):
            config_data = config
        else:
            file_path = Path(config) if isinstance(config, str) else config
            if not file_path.is_file():
                self.logger.error(f"Config file {config} does not exist.")
                raise FileNotFoundError(f"Config file {config} does not exist.")
            config_data = self._load_config_from_file(file_path)
            if not config_data:
                self.logger.error(f"Config file {config} is empty or invalid.")
                raise ValueError(f"Config file {config} is empty or invalid.")

        try:
            validated = schema(**config_data)
        except ValidationError as e:
            self.logger.error(f"Schema validation error: {e}")
            raise

        return validated.model_dump()

    def _validate_environmental_variables(self, config: dict) -> None:
        """
        Validate that all required environmental variables are set according to the schema.
        Args:
            config (dict): Configuration data to validate.
        Raises:
            ValueError: If any required environmental variable is missing.
        """
        required_vars = ["DB_PASSWORD", "LOGGING_PATH"]
        aws_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
        gcp_vars = ["GCP_PROJECT_ID", "GCP_SERVICE_ACCOUNT_KEY"]

        security = config.get("security", {})
        if security and security.get("encryption"):
            required_vars.append("PRIVATE_KEY_PASSWORD")
            if security.get("type") == "kms":
                if security.get("provider") == "aws":
                    required_vars.extend(aws_vars)
            else:
                if security.get("provider") == "gcp":
                    required_vars.extend(gcp_vars)
                elif security.get("provider") == "local":
                    required_vars.append("LOCAL_KEY_STORE_PATH")

        integrity = config.get("integrity", {})
        if (
            integrity
            and integrity.get("integrity_check")
            and integrity.get("integrity_type") == "hmac"
        ):
            required_vars.append("INTEGRITY_PASSWORD")

        storage = config.get("storage", {})
        if storage:
            if storage.get("storage_type") == "aws":
                required_vars.extend(aws_vars)
                required_vars.append("AWS_S3_BUCKET_NAME")
            elif storage.get("storage_type") == "local":
                required_vars.append("LOCAL_PATH")

        for var in required_vars:
            exist = os.getenv(var)
            if not exist:
                self.logger.error(f"Required environmental variable {var} is not set.")
                raise ValueError(f"Required environmental variable {var} is not set.")
            else:
                self.logger.info(f"Environmental variable {var} is set to {exist}.")