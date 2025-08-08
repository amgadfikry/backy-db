# tests/integration_tests/test_metadata_integration.py
import platform
from metadata.extraction_metadata import ExtractionMetadata
from metadata.creation_metadata import CreationMetadata
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()


class TestMetadataIntegration:
    """
    Integration tests for the metadata extraction and creation.
    These tests ensure that the metadata extraction and creation work together correctly.
    """

    def test_creation_of_complete_metadata_then_extract_all_data_from_it(
        self, monkeypatch
    ):
        """
        Test the creation of complete metadata and extraction of all data from it.
        It should create metadata, then extract and verify all metadata components.
        """
        # Create two files in processing path
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "test-bucket")
        monkeypatch.setenv("AWS_REGION", "us-west-2")
        processing_path = Path(os.getenv("MAIN_BACKUP_PATH"))
        backy_file = processing_path / "test_backup.backy"
        backy_file.write_text("CREATE TABLE test (id INT);")

        # Create configuration that pass to metadata creation
        config = {
            "backup": {
                "backup_type": "backy",
                "backup_description": "Test backup",
                "expiry_date": "2023-12-31",
            },
            "database": {
                "db_type": "PostgreSQL",
                "database_version": "13.3",
                "host": "localhost",
                "port": 5432,
                "user": "test_user",
                "db_name": "test_db",
                "multiple_files": True,
                "features": {"tables": True, "data": True},
                "restore_mode": "backy",
                "conflict_mode": "skip",
            },
            "compression": {
                "compression": True,
                "compression_level": 6,
                "compression_type": "zip",
            },
            "security": {
                "encryption": True,
                "type": "keystore",
                "provider": "aws",
                "key_size": 2048,
            },
            "integrity": {
                "integrity_check": True,
                "integrity_type": "checksum",
            },
            "storage": {
                "storage_type": "aws",
            },
        }

        # Create metadata creation instance
        creation_metadata = CreationMetadata(config=config)
        key_id = "backy_secret_key_1"
        version = "8.0.0"
        object_key = "backy_object_key_1"

        # Generate metadata
        backup_metadata = creation_metadata.create_metadata_file(
            version=version, key_id=key_id, object_key=object_key
        )
        assert backup_metadata is not None
        assert Path(backup_metadata).exists()

        # Extract metadata
        extraction_metadata = ExtractionMetadata()
        print(f"Extracted metadata from: {extraction_metadata.metadata}")

        # Extract general metadata and verify
        general_metadata = extraction_metadata.get_general_metadata()
        assert general_metadata["creation_time"] is not None
        assert general_metadata["platform"] == platform.platform()
        assert general_metadata["machine"] == platform.machine()
        assert general_metadata["system"] == platform.system()
        assert general_metadata["os_version"] == platform.version()
        assert general_metadata["python_version"] == platform.python_version()

        # Extract backup metadata and verify
        backup_metadata = extraction_metadata.get_backup_metadata()
        assert backup_metadata["backup_id"] is not None
        assert backup_metadata["backup_time"] is not None
        assert backup_metadata["total_files"] == 1
        assert backup_metadata["files"] == [str(backy_file.name)]
        assert backup_metadata["total_size"] == len(backy_file.read_text())
        assert backup_metadata["backup_type"] == "backy"
        assert backup_metadata["backup_description"] == "Test backup"
        assert backup_metadata["expiry_date"] == "2023-12-31"

        # Extract database metadata and verify
        database_metadata = extraction_metadata.get_database_metadata()
        assert database_metadata["db_type"] == config["database"]["db_type"]
        assert database_metadata["db_version"] == version
        assert database_metadata["host"] == config["database"]["host"]
        assert database_metadata["port"] == config["database"]["port"]
        assert database_metadata["user"] == config["database"]["user"]
        assert database_metadata["db_name"] == config["database"]["db_name"]
        assert (
            database_metadata["multiple_files"] == config["database"]["multiple_files"]
        )
        assert database_metadata["features"] == config["database"]["features"]
        assert database_metadata["restore_mode"] == "backy"
        assert database_metadata["conflict_mode"] == "skip"

        # Extract compression metadata and verify
        compression_metadata = extraction_metadata.get_compression_metadata()
        assert compression_metadata["compression"] is True
        assert compression_metadata["compression_level"] == 6
        assert compression_metadata["compression_type"] == "zip"

        # Extract security metadata and verify
        security_metadata = extraction_metadata.get_security_metadata()
        assert security_metadata["encryption"] is True
        assert security_metadata["type"] == "keystore"
        assert security_metadata["provider"] == "aws"
        assert security_metadata["key_size"] == 2048
        assert security_metadata["key_version"] == key_id.split("_")[-1]
        assert security_metadata["encryption_file"] == f"{key_id}.enc"

        # Extract integrity metadata and verify
        integrity_metadata = extraction_metadata.get_integrity_metadata()
        assert integrity_metadata["integrity_check"] is True
        assert integrity_metadata["integrity_type"] == "checksum"

        # Extract storage metadata and verify
        storage_metadata = extraction_metadata.get_storage_metadata()
        assert storage_metadata["storage_type"] == "aws"
        assert storage_metadata["object_key"] == object_key
        assert storage_metadata["bucket_name"] == os.getenv("AWS_S3_BUCKET_NAME")
        assert storage_metadata["region"] == os.getenv("AWS_REGION")
