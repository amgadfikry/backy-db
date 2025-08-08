# tests/integration_tests/test_config_schema_integration.py
from config_schemas.validator import Validator
import pytest
import yaml


class TestConfigSchemaIntegration:
    """
    Integration tests for the configuration schema validation.
    These tests ensure that the Validator class correctly validates configurations
    for different components of the Backy project.
    """

    @pytest.fixture
    def setup_method(self, monkeypatch):
        """
        Setup method to initialize the Validator and sample configuration data.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("PRIVATE_KEY_PASSWORD", "test_private_key_password")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_aws_access_key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_aws_secret_key")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        monkeypatch.setenv("INTEGRITY_PASSWORD", "test_integrity_password")
        monkeypatch.setenv("LOCAL_PATH", "/backy/local_key_store")

        config_data = {
            "database": {
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "db_name": "backy_db",
            },
            "compression": {
                "compression": True,
                "compression_type": "zip",
            },
            "security": {
                "encryption": True,
                "type": "kms",
                "provider": "aws",
            },
            "integrity": {
                "integrity_check": True,
                "integrity_type": "hmac",
            },
            "storage": {
                "storage_type": "local",
            },
        }
        return config_data

    def test_validate_backup_from_dict(self, setup_method):
        """
        Test validating backup configuration from a dictionary.
        """
        validator = Validator()
        config_data = setup_method
        validated_config = validator.validate_backup(config_data)
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["security"]["provider"] == "aws"
        assert validated_config["backup"]["backup_type"] == "backy"

    def test_validate_backup_from_file(self, tmp_path, setup_method):
        """
        """
        yaml_file = tmp_path / "backup_config.yaml"
        yaml_file.write_text(yaml.dump(setup_method))
        validator = Validator()
        validated_config = validator.validate_backup(str(yaml_file))
        assert isinstance(validated_config, dict)
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["security"]["provider"] == "aws"
        assert validated_config["backup"]["backup_type"] == "backy"
        assert validated_config["storage"]["storage_type"] == "local"

    def test_validate_backup_with_missing_env_vars(self, setup_method):
        """
        Test that validation raises an error when required environment variables are missing.
        """
        validator = Validator()
        config_data = setup_method
        config_data["storage"]["storage_type"] = "aws"
        with pytest.raises(ValueError) as exc_info:
            validator.validate_backup(config_data)
        assert "Required environmental variable AWS_S3_BUCKET_NAME is not set." in str(exc_info.value)

    def test_validate_backup_with_invalid_schema(self, setup_method):
        """
        Test that validation raises an error when the configuration does not match the schema.
        """
        validator = Validator()
        config_data = setup_method
        config_data["database"]["db_type"] = "invalid_db_type"
        with pytest.raises(ValueError) as exc_info:
            validator.validate_backup(config_data)
        assert "validation error" in str(exc_info.value)
        assert "db_type" in str(exc_info.value)

    def test_validate_backup_with_empty_config(self):
        """
        Test that validation raises an error when the configuration is empty.
        """
        validator = Validator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate_backup({})
        assert "validation error" in str(exc_info.value)

    def test_validate_backup_with_required_config_only(self, monkeypatch):
        """
        Test that validation works with only required configuration fields.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        monkeypatch.setenv("LOCAL_PATH", "/backy/local_key_store")
        validator = Validator()
        config_data = {
            "database": {
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "db_name": "backy_db",
            },
            "storage": {
                "storage_type": "local",
            },
        }
        validated_config = validator.validate_backup(config_data)
        assert isinstance(validated_config, dict)
        assert validated_config["backup"]["backup_type"] == "sql"
        assert validated_config["backup"]["backup_description"] == ""
        assert validated_config["database"]["db_type"] == "mysql"
        assert validated_config["storage"]["storage_type"] == "local"
        assert validated_config["security"]["encryption"] is False
        assert validated_config["integrity"]["integrity_check"] is False
        assert validated_config["integrity"]["integrity_type"] == None
        assert validated_config["compression"]["compression"] is False
        assert validated_config["compression"]["compression_type"] == None
