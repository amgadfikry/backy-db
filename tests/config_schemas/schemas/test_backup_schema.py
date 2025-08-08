# tests/config_schemas/schemas/test_backup_schema.py
from config_schemas.schemas.backup_schema import BackupSchema
from config_schemas.schemas.backup_info_schema import BackupInfoSchema
from config_schemas.schemas.database_schema import DatabaseSchema
from config_schemas.schemas.compression_schema import CompressionSchema
from config_schemas.schemas.security_schema import SecuritySchema
from config_schemas.schemas.storage_schema import StorageSchema


class TestBackupSchema:
    """
    Test cases for BackupSchema.
    This class contains tests to validate the BackupSchema
    and ensure it behaves as expected.
    """

    def test_backup_schema_with_default_values(self):
        """
        Test BackupSchema with default values.
        """
        schema = BackupSchema(
            database=DatabaseSchema(
                db_type="mysql",
                db_name="test_db",
                user="test_user",
                port=3306,
                host="localhost",
            ),
            storage=StorageSchema(storage_type="local"),
        )
        assert schema.backup.backup_type == "sql"
        assert schema.database.restore_mode == "sql"
        assert schema.compression.compression is False
        assert schema.security.encryption is False
        assert schema.integrity.integrity_check is False

    def test_backup_schema_with_compression(self):
        """
        Test BackupSchema with compression enabled.
        """
        schema = BackupSchema(
            backup=BackupInfoSchema(backup_type="backy"),
            database=DatabaseSchema(
                db_type="mysql",
                db_name="test_db",
                user="test_user",
                port=3306,
                host="localhost",
            ),
            compression=CompressionSchema(compression=True, compression_type="zip"),
            storage=StorageSchema(storage_type="local"),
        )
        assert schema.backup.backup_type == "backy"
        assert schema.database.restore_mode == "backy"
        assert schema.compression.compression is True

    def test_backup_schema_with_encryption(self):
        """
        Test BackupSchema with encryption enabled.
        """
        schema = BackupSchema(
            backup=BackupInfoSchema(backup_type="backy"),
            database=DatabaseSchema(
                db_type="mysql",
                db_name="test_db",
                user="test_user",
                port=3306,
                host="localhost",
            ),
            security=SecuritySchema(encryption=True, type="keystore", provider="gcp"),
            storage=StorageSchema(storage_type="local"),
        )
        assert schema.backup.backup_type == "backy"
        assert schema.database.restore_mode == "backy"
        assert schema.security.encryption is True
