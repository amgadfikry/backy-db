# tests/metadata/test_extraction_metadata.py
import pytest
from metadata.extraction_metadata import ExtractionMetadata
import json
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class TestExtractionMetadata:
    """
    Test suite for the ExtractionMetadata class.
    This class tests the functionality of extracting metadata from backup files.
    """

    @pytest.fixture(autouse=True)
    def setup_metadata(self, tmp_path):
        """
        Fixture to set up a temporary metadata file for testing.
        Args:
            tmp_path (Path): The temporary directory provided by pytest.
        """
        process_path = os.getenv("MAIN_BACKUP_PATH")
        metadata_file = Path(process_path) / "test_metadata.backy.json"
        metadata_content = {
            "info": {"info": "test"},
            "backup": {"backup": "test"},
            "database": {"database": "test"},
            "compression": {"compression": "test"},
            "security": {"security": "test"},
            "integrity": {"integrity": "test"},
            "storage": {"storage": "test"},
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata_content, f)
        self.content = metadata_content

    def test_initialize_extraction_metadata(self):
        """
        Test the initialization of the ExtractionMetadata class.
        It should load the metadata from the specified file.
        """
        metadata = ExtractionMetadata()
        assert isinstance(metadata.metadata, dict)
        assert metadata.metadata == self.content

    def test_load_metadata_sucess(self):
        """
        Test the _load_metadata method.
        It should return the loaded metadata from the file.
        """
        metadata = ExtractionMetadata()
        assert metadata._load_metadata() == self.content

    def test_load_metadata_file_not_found(self, tmp_path, monkeypatch, caplog):
        """
        Test the _load_metadata method when the metadata file does not exist.
        It should return an empty dictionary and log a warning.
        """
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(tmp_path))
        metadata = ExtractionMetadata()
        assert metadata._load_metadata() == {}
        assert "There is no metadata file at working directory" in caplog.text

    def test_load_metadata_error(self, mocker, caplog):
        """
        Test the _load_metadata method when there is an error reading the file.
        It should log a warning and return an empty dictionary.
        """
        mocker.patch("builtins.open", side_effect=IOError("File not found"))
        metadata = ExtractionMetadata()
        assert metadata._load_metadata() == {}
        assert "Error reading metadata file" in caplog.text

    def test_get_general_metadata(self):
        """
        Test the get_general_metadata method.
        It should return the general metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_general_metadata() == self.content["info"]

    def test_get_backup_metadata(self):
        """
        Test the get_backup_metadata method.
        It should return the backup metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_backup_metadata() == self.content["backup"]

    def test_get_database_metadata(self):
        """
        Test the get_database_metadata method.
        It should return the database metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_database_metadata() == self.content["database"]

    def test_get_compression_metadata(self):
        """
        Test the get_compression_metadata method.
        It should return the compression metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_compression_metadata() == self.content["compression"]

    def test_get_security_metadata(self):
        """
        Test the get_security_metadata method.
        It should return the security metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_security_metadata() == self.content["security"]

    def test_get_integrity_metadata(self):
        """
        Test the get_integrity_metadata method.
        It should return the integrity metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_integrity_metadata() == self.content["integrity"]

    def test_get_storage_metadata(self):
        """
        Test the get_storage_metadata method.
        It should return the storage metadata from the loaded metadata.
        """
        metadata = ExtractionMetadata()
        assert metadata.get_storage_metadata() == self.content["storage"]

    def test_get_all_metadata(self):
        """
        Test the get_all_metadata method.
        It should return all metadata as a dictionary.
        """
        metadata = ExtractionMetadata()
        all_metadata = metadata.get_full_metadata()
        assert isinstance(all_metadata, dict)
        assert all_metadata == self.content
