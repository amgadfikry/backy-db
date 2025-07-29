# tests/schema/test_backup_schema.py
import pytest
from schema.backup_schema import (
    DatabaseConfig,
    StorageConfig,
    CompressionConfig,
    SecurityConfig,
    BackupConfig,
)


class TestBackupSchema:
    """
    Tests for the backup schema.
    """

    @pytest.fixture
    def valid_config(self):
        """
        Fixture for a valid backup configuration with minimal settings required.
        """
        return {
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_pass",
                "db_name": "test_db",
                "db_type": "mysql",
            },
            "storage": {
                "path": "/backups",
            },
        }

    def test_valid_and_default_database_config(self, valid_config):
        """
        Test that a valid database configuration is accepted. and defaults are set correctly.
        """
        config = DatabaseConfig(**valid_config["database"])
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.db_name == "test_db"
        assert config.db_type == "mysql"
        assert config.one_file is True
        assert config.tables is True
        assert config.data is True
        assert config.triggers is False
        assert config.views is False
        assert config.functions is False
        assert config.procedures is False
        assert config.events is False

    def test_invalid_database_config(self, valid_config):
        """
        Test that an invalid database configuration raises a validation error.
        """
        valid_config["database"]["db_type"] = "invalid_db_type"
        with pytest.raises(ValueError):
            config = DatabaseConfig(**valid_config["database"])
            assert config is None

    def test_missing_required_fields(self, valid_config):
        """
        Test that missing required fields in the database configuration raises a validation error.
        """
        del valid_config["database"]["host"]
        with pytest.raises(ValueError):
            config = DatabaseConfig(**valid_config["database"])
            assert config is None

    def test_valid_and_default_storage_config(self, valid_config):
        """
        Test that a valid storage configuration is accepted.
        """
        config = StorageConfig(**valid_config["storage"])
        assert config.storage_type == "local"
        assert config.path == "/backups"

    def test_valid_and_default_compression_config(self):
        """
        Test that a valid compression configuration is accepted with defaults.
        """
        config = CompressionConfig()
        assert config.compression is False
        assert config.compression_type is None

    def test_compression_is_true_without_type(self, caplog):
        """
        Test that compression cannot be true without a compression type.
        """
        with caplog.at_level("WARNING"):
            config = CompressionConfig(compression=True)
            assert config.compression is True
            assert "Compression type is not set, defaulting to 'zip'." in caplog.text
            assert config.compression_type == "zip"

    def test_security_defaults_values(self):
        """
        Test that security configuration defaults are set correctly.
        """
        config = SecurityConfig()
        assert config.encryption is False
        assert config.private_key_size is None
        assert config.private_key_password is None
        assert config.private_key_size is None
        assert config.integrity_check is False
        assert config.integrity_password is None
        assert config.file_extension is None

    def test_security_encryption_without_password(self, caplog):
        """
        Test that enabling encryption without a password raises an error.
        """
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                config = SecurityConfig(encryption=True)
                assert config.encryption is True
                assert (
                    "Private key password must be set if encryption is enabled."
                    in caplog.text
                )
                assert config.private_key_password is None

    def test_security_encryption_with_default_size(self, caplog):
        """
        Test that enabling encryption without a private key size defaults to '4096'.
        """
        with caplog.at_level("WARNING"):
            config = SecurityConfig(encryption=True, private_key_password="test_pass")
            assert config.private_key_size == "4096"
            assert "Private key size is not set, defaulting to '4096'." in caplog.text

    def test_security_integrity_check_without_password(self, caplog):
        """
        Test that enabling integrity check without a password raises an error.
        """
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                config = SecurityConfig(
                    encryption=True,
                    integrity_check=True,
                    private_key_password="test_pass",
                )
                assert config.integrity_check is True
                assert (
                    "Integrity password must be set if integrity check is enabled."
                    in caplog.text
                )
                assert config.integrity_password is None

    def test_security_integrity_check_without_encryption(self, caplog):
        """
        Test that integrity check cannot be enabled without encryption.
        """
        with caplog.at_level("WARNING"):
            config = SecurityConfig(integrity_check=True)
            assert config.integrity_check is False
            assert (
                "Integrity check cannot be performed without encryption. Disabling integrity check."
                in caplog.text
            )

    def test_backup_config_combined(self, valid_config):
        """
        Test that a complete backup configuration is valid and combines all settings.
        """
        valid_config["security"] = {
            "encryption": True,
            "private_key_password": "test_pass",
        }
        valid_config["compression"] = {
            "compression": True,
            "compression_type": "tar",
        }
        backup_config = BackupConfig(**valid_config)
        assert backup_config.database.host == "localhost"
        assert backup_config.storage.path == "/backups"
        assert backup_config.compression.compression is True
        assert backup_config.security.encryption is True

    def test_backup_config_missing_security_and_compression(self, valid_config):
        """
        Test that a backup configuration without security and compression settings is valid.
        """
        backup_config = BackupConfig(**valid_config)
        assert backup_config.security.encryption is False
        assert backup_config.compression.compression is False
        assert backup_config.database.host == "localhost"
        assert backup_config.storage.path == "/backups"

    def test_backup_config_with_encryption_and_no_compression(self, valid_config):
        """
        Test that a backup configuration with encryption but no compression is valid.
        """
        valid_config["security"] = {
            "encryption": True,
            "private_key_password": "test_pass",
            "private_key_size": "2048",
            "integrity_check": True,
            "integrity_password": "integrity_pass",
        }
        backup_config = BackupConfig(**valid_config)
        assert backup_config.security.encryption is False
        assert backup_config.compression.compression is False
        assert backup_config.security.private_key_size is None
        assert backup_config.security.integrity_check is False
        assert backup_config.security.integrity_password is None
        assert backup_config.security.private_key_password is None

    def test_security_file_extension_when_compression(self, valid_config):
        """
        Test that the file extension is set correctly when compression is enabled.
        """
        valid_config["compression"] = {
            "compression": True,
            "compression_type": "zip",
        }
        valid_config["security"] = {
            "encryption": True,
            "private_key_password": "test_pass",
        }
        backup_config = BackupConfig(**valid_config)
        assert backup_config.compression.compression_type == "zip"
        assert backup_config.security.file_extension == "zip"
        assert backup_config.security.encryption is True
