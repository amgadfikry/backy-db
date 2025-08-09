# tests/config_schemas/test_validator.py
from config_schemas.validator import Validator
import pytest
import yaml
import json
from pydantic import ValidationError


class TestValidator:
    """
    Test cases for Validator class.
    This class contains tests to validate the Validator's functionality
    for backup and restore configurations.
    """

    def setup_method(self):
        """
        Setup method to initialize the Validator instance.
        """
        self.validator = Validator()
        self.config_data = {
            "database": {
                "db_type": "mysql",
                "db_name": "test_db",
                "user": "test_user",
                "port": 3306,
                "host": "localhost",
            },
            "storage": {"storage_type": "local"},
        }
        self.env_config = {
            "security": {
                "encryption": True,
                "type": "kms",
                "provider": "aws",
                "key_size": 2048,
                "key_version": "v1",
            },
            "integrity": {"integrity_check": True, "integrity_type": "checksum"},
            "storage": {
                "storage_type": "local",
            },
        }

    def test_load_config_from_yaml_file(self, tmp_path):
        """
        Test loading configuration from a file.
        This test checks if the Validator can load a configuration file correctly.
        """
        # Assuming a valid YAML or JSON file path is provided
        file_path = tmp_path / "backup_config.yaml"
        file_path.write_text(yaml.dump(self.config_data))
        config_data = self.validator._load_config_from_file(file_path)
        assert isinstance(config_data, dict)
        assert "database" in config_data
        assert config_data["database"]["db_type"] == "mysql"
        assert "storage" in config_data

    def test_load_config_from_yml_file(self, tmp_path):
        """
        Test loading configuration from a YAML file.
        This test checks if the Validator can load a configuration file correctly.
        """
        # Assuming a valid YAML file path is provided
        file_path = tmp_path / "backup_config.yml"
        file_path.write_text(yaml.dump(self.config_data))
        config_data = self.validator._load_config_from_file(file_path)
        assert isinstance(config_data, dict)
        assert "database" in config_data
        assert config_data["database"]["db_type"] == "mysql"
        assert "storage" in config_data

    def test_load_config_from_json_file(self, tmp_path):
        """
        Test loading configuration from a JSON file.
        This test checks if the Validator can load a configuration file correctly.
        """
        # Assuming a valid JSON file path is provided
        file_path = tmp_path / "backup_config.json"
        file_path.write_text(json.dumps(self.config_data, indent=4))
        config_data = self.validator._load_config_from_file(file_path)
        assert isinstance(config_data, dict)
        assert "database" in config_data
        assert config_data["database"]["db_type"] == "mysql"
        assert config_data["storage"]["storage_type"] == "local"

    def test_load_config_from_unsupported_file(self, tmp_path):
        """
        Test loading configuration from an unsupported file format.
        This test checks if the Validator raises a ValueError for unsupported formats.
        """
        file_path = tmp_path / "backup_config.txt"
        file_path.write_text("This is not a valid config file.")
        with pytest.raises(ValueError) as exc_info:
            self.validator._load_config_from_file(file_path)
        assert "Unsupported file format: .txt" in str(exc_info.value)

    def test_validate_according_type_with_valid_dict(self):
        """
        Test validating a configuration dict against a schema.
        This test checks if the Validator can validate a dict correctly.
        """
        validated_config = self.validator._validate_according_type(
            self.config_data, "backup"
        )
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_according_type_with_valid_file(self, mocker, tmp_path):
        """
        Test validating a configuration file against a schema.
        This test checks if the Validator can validate a file correctly.
        """
        file_path = tmp_path / "backup_config.json"
        file_path.touch()
        mocker.patch.object(
            self.validator, "_load_config_from_file", return_value=self.config_data
        )
        validated_config = self.validator._validate_according_type(file_path, "backup")
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_according_type_with_str_json(self, tmp_path, mocker):
        """
        Test validating a configuration file path as a string.
        This test checks if the Validator can validate a string path correctly.
        """
        file_path = tmp_path / "backup_config.json"
        file_path.touch()
        mocker.patch.object(
            self.validator, "_load_config_from_file", return_value=self.config_data
        )
        validated_config = self.validator._validate_according_type(
            str(file_path), "backup"
        )
        assert isinstance(validated_config, dict)
        assert validated_config["backup"]["backup_type"] == "sql"
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_according_type_with_invalid_file(self, tmp_path):
        """
        Test validating a non-existent file.
        This test checks if the Validator raises a FileNotFoundError for non-existent files.
        """
        file_path = tmp_path / "non_existent_config.json"
        with pytest.raises(FileNotFoundError) as exc_info:
            self.validator._validate_according_type(file_path, "backup")
        assert f"Config file {file_path} does not exist." in str(exc_info.value)

    def test_validate_according_type_with_empty_file(self, tmp_path, mocker):
        """
        Test validating an empty configuration file.
        This test checks if the Validator raises a ValueError for empty files.
        """
        file_path = tmp_path / "empty_config.json"
        file_path.touch()
        mocker.patch.object(self.validator, "_load_config_from_file", return_value={})
        with pytest.raises(ValueError) as exc_info:
            self.validator._validate_according_type(file_path, "backup")
        assert f"Config file {file_path} is empty or invalid." in str(exc_info.value)

    def test_validate_according_type_with_invalid_schema(self, mocker):
        """
        Test validating a configuration dict against an invalid schema.
        This test checks if the Validator raises a ValidationError for invalid schemas.
        """
        invalid_config = {"invalid_key": "value"}
        with pytest.raises(ValidationError) as exc_info:
            self.validator._validate_according_type(invalid_config, "backup")
        assert "validation error" in str(exc_info.value)

    def test_validate_backup_with_valid_dict(self, mocker):
        """
        Test validating a backup configuration dict.
        This test checks if the Validator can validate a backup dict correctly.
        """
        mocker.patch.object(
            self.validator, "_validate_according_type", return_value=self.config_data
        )
        mocker.patch.object(
            self.validator, "_validate_environmental_variables", return_value=None
        )
        validated_config = self.validator.validate_backup(self.config_data)
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_environmental_variables_with_missing_required_keys(self):
        """
        Test validating environmental variables with missing required keys.
        This test checks if the Validator raises a ValueError for missing keys.
        """
        with pytest.raises(ValueError) as exc_info:
            self.validator._validate_environmental_variables(self.env_config)
        assert "Required environmental variable DB_PASSWORD is not set." in str(
            exc_info.value
        )

    def test_validate_environmental_variables_all_required_keys_set(self, monkeypatch):
        """
        Test validating environmental variables with all required keys set.
        This test checks if the Validator does not raise an error when all required keys are present.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        self.env_config["security"]["encryption"] = False
        self.env_config["integrity"]["integrity_check"] = False
        self.env_config["storage"]["storage_type"] = "local"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_kms_provider(self, monkeypatch):
        """
        Test validating environmental variables with KMS provider.
        This test checks if the Validator can validate KMS-specific variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "aws_access_key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret_key")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        self.env_config["security"]["encryption"] = True
        self.env_config["security"]["type"] = "kms"
        self.env_config["security"]["provider"] = "aws"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_gcp_provider(self, monkeypatch):
        """
        Test validating environmental variables with GCP provider.
        This test checks if the Validator can validate GCP-specific variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        monkeypatch.setenv("GCP_PROJECT_ID", "gcp_project_id")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "gcp_service_account_key")
        self.env_config["security"]["encryption"] = True
        self.env_config["security"]["type"] = "keystore"
        self.env_config["security"]["provider"] = "gcp"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_local_provider(self, monkeypatch):
        """
        Test validating environmental variables with local provider.
        This test checks if the Validator can validate local-specific variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", "/local/keystore")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        self.env_config["security"]["encryption"] = True
        self.env_config["security"]["type"] = "keystore"
        self.env_config["security"]["provider"] = "local"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_integrity_check(self, monkeypatch):
        """
        Test validating environmental variables with integrity check.
        This test checks if the Validator can validate integrity-specific variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("INTEGRITY_PASSWORD", "integrity_password")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        self.env_config["security"]["encryption"] = False
        self.env_config["integrity"]["integrity_check"] = True
        self.env_config["integrity"]["integrity_type"] = "hmac"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_missing_integrity_password(
        self, monkeypatch
    ):
        """
        Test validating environmental variables with missing integrity password.
        This test checks if the Validator raises a ValueError for missing integrity password.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        self.env_config["security"]["encryption"] = False
        self.env_config["integrity"]["integrity_check"] = True
        self.env_config["integrity"]["integrity_type"] = "hmac"
        with pytest.raises(ValueError) as exc_info:
            self.validator._validate_environmental_variables(self.env_config)
        assert "Required environmental variable INTEGRITY_PASSWORD is not set." in str(
            exc_info.value
        )

    def test_validate_environmental_variables_with_aws_storage(self, monkeypatch):
        """
        Test validating environmental variables with AWS storage.
        This test checks if the Validator can validate AWS-specific storage variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "aws_access_key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "aws_secret_key")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "my_bucket")
        self.env_config["storage"]["storage_type"] = "aws"
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_local_storage(self, monkeypatch):
        """
        Test validating environmental variables with local storage.
        This test checks if the Validator can validate local-specific storage variables correctly.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        monkeypatch.setenv("LOCAL_PATH", "/backups")
        self.env_config["storage"]["storage_type"] = "local"
        self.env_config["security"]["encryption"] = False
        self.env_config["integrity"]["integrity_check"] = False
        self.validator._validate_environmental_variables(self.env_config)
        assert True

    def test_validate_environmental_variables_with_missing_aws_keys(self, monkeypatch):
        """
        Test validating environmental variables with missing AWS keys.
        This test checks if the Validator raises a ValueError for missing AWS keys.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        self.env_config["storage"]["storage_type"] = "aws"
        with pytest.raises(ValueError) as exc_info:
            self.validator._validate_environmental_variables(self.env_config)
        assert "Required environmental variable AWS_ACCESS_KEY_ID is not set." in str(
            exc_info.value
        )

    def test_validate_environmental_variables_with_missing_local_path(
        self, monkeypatch
    ):
        """
        Test validating environmental variables with missing local path.
        This test checks if the Validator raises a ValueError for missing local path.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOGGING_PATH", "/var/logs")
        self.env_config["security"]["encryption"] = False
        self.env_config["integrity"]["integrity_check"] = False
        self.env_config["storage"]["storage_type"] = "local"
        with pytest.raises(ValueError) as exc_info:
            self.validator._validate_environmental_variables(self.env_config)
        assert "Required environmental variable LOCAL_PATH is not set." in str(
            exc_info.value
        )

    def test_validate_restore_with_valid_dict(self, mocker):
        """
        Test validating a restore configuration dict.
        This test checks if the Validator can validate a restore dict correctly.
        """
        mocker.patch.object(
            self.validator, "_validate_according_type", return_value=self.config_data
        )
        mocker.patch.object(
            self.validator, "_validate_environmental_variables", return_value=None
        )
        validated_config = self.validator.validate_restore(self.config_data)
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_restore_metadata_with_valid_dict(self, mocker):
        """
        Test validating restore metadata with a valid configuration dict.
        This test checks if the Validator can validate restore metadata correctly.
        """
        mocker.patch.object(
            self.validator, "_validate_environmental_variables", return_value=None
        )
        self.validator.validate_restore_metadata(self.config_data)
        assert True
