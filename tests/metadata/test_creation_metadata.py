# tests/metadata/test_creation_metadata.py
import pytest
from metadata.creation_metadata import CreationMetadata
from pathlib import Path
import json


class TestCreationMetadata:
    """
    This class contains tests for the methods that generate metadata
    for the creation process of backups.
    """

    def test_generate_general_metadata(self):
        """
        Test the generation of general metadata.
        """
        config = {}
        metadata = CreationMetadata(config)
        general_metadata = metadata.generate_general_metadata()

        assert "creation_time" in general_metadata
        assert "platform" in general_metadata
        assert "machine" in general_metadata
        assert "system" in general_metadata
        assert "os_version" in general_metadata
        assert "python_version" in general_metadata

    def test_generate_backup_metadata(self):
        """
        Test the generation of backup metadata.
        """
        config = {}
        metadata = CreationMetadata(config)
        sql_file = Path(metadata.processing_path) / "test_backup.sql"
        sql_file.write_text("This is a test SQL backup file.")
        backy_file = Path(metadata.processing_path) / "test_backup.backy"
        backy_file.write_text("This is a test Backy backup file.")
        other_file = Path(metadata.processing_path) / "test_other.txt"
        other_file.touch()

        backup_metadata = metadata.generate_backup_metadata()

        assert "backup_id" in backup_metadata
        assert "backup_time" in backup_metadata
        assert backup_metadata["total_files"] == 2
        assert backup_metadata["files"] == [sql_file.name, backy_file.name]
        assert "total_size" in backup_metadata
        assert backup_metadata["total_size"] > 0
        assert "backup_type" in backup_metadata
        assert "backup_description" in backup_metadata
        assert "expiry_date" in backup_metadata

    def test_generate_database_metadata(self):
        """
        Test the generation of database metadata.
        """
        config = {}
        metadata = CreationMetadata(config)
        version = "1.0.0"
        database_metadata = metadata.generate_database_metadata(version)

        assert "db_type" in database_metadata
        assert "db_version" in database_metadata
        assert "host" in database_metadata
        assert "port" in database_metadata
        assert "user" in database_metadata
        assert "db_name" in database_metadata
        assert "multiple_files" in database_metadata
        assert "features" in database_metadata
        assert "restore_mode" in database_metadata
        assert "conflict_mode" in database_metadata

    def test_generate_compression_metadata(self):
        """
        Test the generation of compression metadata.
        """
        config = {}
        metadata = CreationMetadata(config)
        compression_metadata = metadata.generate_compression_metadata()

        assert "compression_type" in compression_metadata
        assert "compression_level" in compression_metadata
        assert "compression" in compression_metadata

    def test_generate_security_metadata_if_there_is_key_id(self):
        """
        Test the generation of security metadata.
        """
        config = {}
        key_id = "backy_secret_key_1"
        metadata = CreationMetadata(config)
        security_metadata = metadata.generate_security_metadata(key_id)

        assert "encryption" in security_metadata
        assert "type" in security_metadata
        assert "provider" in security_metadata
        assert "key_size" in security_metadata
        assert security_metadata["key_version"] == "1"
        assert security_metadata["encryption_file"] == "backy_secret_key_1.enc"

    def test_generate_security_metadata_if_there_is_no_key_id(self):
        """
        Test the generation of security metadata when there is no key ID.
        """
        config = {}
        key_id = ""
        metadata = CreationMetadata(config)
        security_metadata = metadata.generate_security_metadata(key_id)

        assert "encryption" in security_metadata
        assert "type" in security_metadata
        assert "provider" in security_metadata
        assert "key_size" in security_metadata
        assert security_metadata["key_version"] is None
        assert security_metadata["encryption_file"] is None

    def test_generate_integrity_metadata(self):
        """
        Test the generation of integrity metadata.
        """
        config = {}
        metadata = CreationMetadata(config)
        integrity_metadata = metadata.generate_integrity_metadata()

        assert "integrity_check" in integrity_metadata
        assert "integrity_type" in integrity_metadata

    def test_generate_storage_metadata_with_local_storage(self):
        """
        Test the generation of storage metadata with local storage.
        """
        config = {"storage": {"storage_type": "local"}}
        metadata = CreationMetadata(config)
        object_key = "test_object_key"
        storage_metadata = metadata.generate_storage_metadata(object_key)

        assert storage_metadata["storage_type"] == "local"
        assert storage_metadata["object_key"] == object_key
        assert storage_metadata["bucket_name"] is None
        assert storage_metadata["region"] is None

    def test_generate_storage_metadata_with_s3_storage(self, monkeypatch):
        """
        Test the generation of storage metadata with S3 storage.
        """
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "test_bucket")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        config = {"storage": {"storage_type": "aws"}}
        metadata = CreationMetadata(config)
        object_key = "test_object_key"
        storage_metadata = metadata.generate_storage_metadata(object_key)

        assert storage_metadata["storage_type"] == "aws"
        assert storage_metadata["object_key"] == object_key
        assert storage_metadata["bucket_name"] == "test_bucket"
        assert storage_metadata["region"] == "us-west-2"

    def test_generate_full_metadata(self, mocker):
        """
        Test the generation of full metadata.
        """
        config = {}
        version = "1.0.0"
        key_id = "backy_secret_key_1"
        object_key = "test_object_key"
        metadata = CreationMetadata(config)
        mocker.patch.object(metadata, "generate_general_metadata", return_value={})
        mocker.patch.object(metadata, "generate_backup_metadata", return_value={})
        mocker.patch.object(metadata, "generate_database_metadata", return_value={})
        mocker.patch.object(metadata, "generate_compression_metadata", return_value={})
        mocker.patch.object(metadata, "generate_security_metadata", return_value={})
        mocker.patch.object(metadata, "generate_integrity_metadata", return_value={})
        mocker.patch.object(metadata, "generate_storage_metadata", return_value={})

        full_metadata = metadata.generate_full_metadata(version, key_id, object_key)

        assert isinstance(full_metadata, dict)
        assert "info" in full_metadata
        assert "backup" in full_metadata
        assert "database" in full_metadata
        assert "compression" in full_metadata
        assert "security" in full_metadata
        assert "integrity" in full_metadata
        assert "storage" in full_metadata

        metadata.generate_general_metadata.assert_called_once()
        metadata.generate_backup_metadata.assert_called_once()
        metadata.generate_database_metadata.assert_called_once()
        metadata.generate_compression_metadata.assert_called_once()
        metadata.generate_security_metadata.assert_called_once()
        metadata.generate_integrity_metadata.assert_called_once()
        metadata.generate_storage_metadata.assert_called_once()

    def test_create_metadata_file_success(self):
        """
        Test the creation of a metadata file.
        """
        config = {"database": {"db_name": "test_db"}}
        version = "1.0.0"
        key_id = "backy_secret_key_1"
        object_key = "test_object_key"

        metadata = CreationMetadata(config)
        metadata_file_path = metadata.create_metadata_file(version, key_id, object_key)

        assert Path(metadata_file_path).exists()
        assert Path(metadata_file_path).is_file()
        assert Path(metadata_file_path).name.startswith("test_db_")
        assert Path(metadata_file_path).name.endswith("_metadata.backy.json")

        with open(metadata_file_path, "r") as f:
            content = f.read()
            assert content.startswith("{") and content.endswith("}")
            metadata_dict = json.loads(content)
            assert "info" in metadata_dict
            assert "backup" in metadata_dict
            assert "database" in metadata_dict
            assert "compression" in metadata_dict
            assert "security" in metadata_dict
            assert "integrity" in metadata_dict
            assert "storage" in metadata_dict

    def test_create_metadata_file_failure(self, mocker):
        """
        Test the failure of metadata file creation due to missing config.
        """
        config = {}
        version = "1.0.0"
        key_id = "backy_secret_key_1"
        object_key = "test_object_key"

        metadata = CreationMetadata(config)
        mocker.patch("builtins.open", side_effect=RuntimeError("Missing config"))
        with pytest.raises(RuntimeError) as exc_info:
            metadata.create_metadata_file(version, key_id, object_key)
        assert "Failed to create metadata file: Missing config" in str(exc_info.value)
