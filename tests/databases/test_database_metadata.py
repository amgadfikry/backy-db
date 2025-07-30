# tests/databases/test_database_metadata.py
import shutil
import pytest
import tempfile
from pathlib import Path
import json
from databases.database_metadata import DatabaseMetadata
import hashlib


class TestDatabaseMetadata:
    """
    Test suite for the DatabaseMetadata class.
    This class tests the functionality of the DatabaseMetadata class, including
    creating backup folders, metadata files, and checksum files.
    """

    @pytest.fixture
    def setup_method(self, monkeypatch):
        """
        Fixture to provide a mock configuration for the database.
        """
        temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("LOGGING_PATH", temp_dir)
        backup_path = Path(temp_dir) / "backups"
        backup_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("MAIN_BACKUP_PATH", backup_path)

        config = {
            "db_type": "test_db_type",
            "version": "1.0",
            "db_name": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
            "tables": True,
            "data": True,
            "views": True,
            "functions": True,
            "procedures": True,
            "triggers": True,
            "events": True,
        }
        metadata_database = DatabaseMetadata(config=config)
        yield metadata_database, backup_path
        # Cleanup after the test
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_backup_folder_sucessfully(self, setup_method):
        """
        Test the creation of a backup folder with a valid timestamp.
        """
        metadata_database, backup_path = setup_method
        assert metadata_database.backup_folder_path == backup_path
        timestamp = "2023-10-01_12-00-00"
        backup_folder = metadata_database.create_backup_folder(timestamp)
        assert backup_folder.exists()
        assert backup_folder.name == f"{metadata_database.db_name}_{timestamp}_backup"
        assert metadata_database.backup_folder_path == backup_folder

    def test_create_backup_folder_failure(self, setup_method, mocker, caplog):
        """
        Test the failure of backup folder creation when an error occurs.
        """
        metadata_database, _ = setup_method
        mocker.patch("pathlib.Path.mkdir", side_effect=Exception("Mocked error"))
        with pytest.raises(RuntimeError) as exc_info:
            metadata_database.create_backup_folder("2023-10-01_12-00-00")
        assert "Failed to create backup folder" in str(exc_info.value)
        assert "Error creating backup folder: Mocked error" in caplog.text

    def test_create_metadata_file_successfully(self, setup_method):
        """
        Test the creation of a metadata file with valid backup files.
        """
        metadata_database, backup_path = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        
        # Create a dummy file in the backup folder
        (metadata_database.backup_folder_path / "dummy_file.txt").touch()

        metadata_file = metadata_database.create_metadata_file(timestamp)
        assert metadata_file.exists()
        assert metadata_file.name == f"{metadata_database.db_name}_{timestamp}_metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        assert metadata["db_type"] == metadata_database.db_type
        assert metadata["version"] == metadata_database.version
        assert metadata["timestamp"] == timestamp
        assert metadata["db_name"] == metadata_database.db_name
        assert metadata["host"] == metadata_database.host
        assert metadata["port"] == metadata_database.port
        assert metadata["user"] == metadata_database.user
        assert metadata["backup_folder"] == metadata_database.backup_folder_path.name
        assert metadata["backup_files"] == ["dummy_file.txt"]
        assert metadata["total_backup_size"] == 0
        assert metadata["number_of_files"] == 1
        assert metadata["features"] == {
            "tables": metadata_database.tables,
            "data": metadata_database.data,
            "views": metadata_database.views,
            "functions": metadata_database.functions,
            "procedures": metadata_database.procedures,
            "triggers": metadata_database.triggers,
            "events": metadata_database.events,
        }

    def test_create_metadata_file_no_files(self, setup_method, caplog):
        """
        Test the creation of a metadata file when no backup files are present.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)

        with pytest.raises(FileNotFoundError) as exc_info:
            metadata_database.create_metadata_file(timestamp)
        
        assert str(exc_info.value) == "No backup files found in the backup folder."
        assert "No backup files found to create metadata." in caplog.text

    def test_create_metadata_file_failure(self, setup_method, mocker, caplog):
        """
        Test the failure of metadata file creation when an error occurs.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        # Create a dummy file in the backup folder
        (metadata_database.backup_folder_path / "dummy_file.txt").touch()

        # Mock the open function to raise an error
        mocker.patch("builtins.open", side_effect=Exception("Mocked error"))

        with pytest.raises(RuntimeError) as exc_info:
            metadata_database.create_metadata_file(timestamp)
        
        assert "Failed to create metadata file" in str(exc_info.value)
        assert "Error creating metadata file: Mocked error" in caplog.text

    def test_create_checksum_file_successfully(self, setup_method, mocker):
        """
        Test the creation of a checksum file with valid backup files.
        """
        metadata_database, backup_path = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        
        # Create a dummy file in the backup folder
        (metadata_database.backup_folder_path / "dummy_file1.txt").touch()
        (metadata_database.backup_folder_path / "dummy_file2.txt").touch()
        mocker.patch("databases.database_metadata.generate_sha256", return_value="dummy_checksum")

        checksum_file = metadata_database.create_checksum_file(timestamp)
        assert checksum_file.exists()
        assert checksum_file.name == f"{metadata_database.db_name}_{timestamp}_checksum.sha256"
        
        with open(checksum_file, 'r') as f:
            content = f.read().strip().splitlines()
        assert len(content) == 2
        assert content[0] == "dummy_checksum  dummy_file1.txt"
        assert content[1] == "dummy_checksum  dummy_file2.txt"
        
    def test_create_checksum_file_no_files(self, setup_method, caplog):
        """
        Test the creation of a checksum file when no backup files are present.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)

        with pytest.raises(FileNotFoundError) as exc_info:
            metadata_database.create_checksum_file(timestamp)

        assert str(exc_info.value) == "No backup files found to generate checksums."
        assert "No backup files found to generate checksums." in caplog.text

    def test_create_checksum_file_failure(self, setup_method, mocker, caplog):
        """
        Test the failure of checksum file creation when an error occurs.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        
        # Create a dummy file in the backup folder
        (metadata_database.backup_folder_path / "dummy_file.txt").touch()

        # Mock the open function to raise an error
        mocker.patch("builtins.open", side_effect=Exception("Mocked error"))

        with pytest.raises(RuntimeError) as exc_info:
            metadata_database.create_checksum_file(timestamp)

        assert "Failed to create checksum file" in str(exc_info.value)
        assert "Error creating checksum file: Mocked error" in caplog.text

    def test_verify_checksum_file_successfully(self, setup_method, caplog):
        """
        Test the verification of a checksum file with valid backup files.
        """
        metadata_database, backup_path = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        
        # Create dummy files and a checksum file
        (metadata_database.backup_folder_path / "dummy_file1.txt").write_text("test data 1")
        (metadata_database.backup_folder_path / "dummy_file2.txt").write_text("test data 2")
        
        files = metadata_database.backup_folder_path.glob("*")
        checksum_file = metadata_database.backup_folder_path / f"{metadata_database.db_name}_{timestamp}_checksum.sha256"

        with open(checksum_file, "w", encoding="utf-8") as f:
            for file in files:
                h = hashlib.sha256()
                with open(file, "rb") as ff:
                    while chunk := ff.read(8192):
                        h.update(chunk)
                f.write(f"{h.hexdigest()}  {file.name}\n")

        result = metadata_database.verify_checksum_file()
        assert result is True
        assert "All files verified successfully against checksums." in caplog.text

    def test_verify_checksum_file_no_checksum(self, setup_method, caplog):
        """
        Test the verification of a checksum file when it does not exist.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)

        with pytest.raises(FileNotFoundError) as exc_info:
            metadata_database.verify_checksum_file()

        assert str(exc_info.value) == "Checksum file does not exist."
        assert "Checksum file does not exist." in caplog.text

    def test_verify_checksum_file_when_file_path_not_exist(self, setup_method, caplog):
        """
        Test the verification of a checksum file when a file does not exist.
        """
        metadata_database, backup_path = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)
        
        # Create a dummy checksum file
        checksum_file = metadata_database.backup_folder_path / f"{metadata_database.db_name}_{timestamp}_checksum.sha256"
        checksum_file.write_text("dummy_checksum  non_existent_file.txt\n")

        with pytest.raises(FileNotFoundError) as exc_info:
            metadata_database.verify_checksum_file()

        assert str(exc_info.value) == "File non_existent_file.txt does not exist."
        assert "File non_existent_file.txt does not exist." in caplog.text

    def test_verify_checksum_file_mismatch(self, setup_method, caplog):
        """
        Test the verification of a checksum file when the checksum does not match.
        """
        metadata_database, backup_path = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)

        # Create a dummy file in the backup folder
        (metadata_database.backup_folder_path / "dummy_file.txt").touch()
        checksum_file = metadata_database.backup_folder_path / f"{metadata_database.db_name}_{timestamp}_checksum.sha256"
        checksum_file.write_text("invalid_checksum  dummy_file.txt\n")

        with pytest.raises(ValueError) as exc_info:
            metadata_database.verify_checksum_file()

        assert "Checksum mismatch for dummy_file.txt" in str(exc_info.value)
        assert "Checksum mismatch for dummy_file.txt" in caplog.text

    def test_verify_checksum_file_failure(self, setup_method, mocker, caplog):
        """
        Test the failure of checksum file verification when an error occurs.
        """
        metadata_database, _ = setup_method
        timestamp = "2023-10-01_12-00-00"
        metadata_database.create_backup_folder(timestamp)

        # Create a dummy checksum file
        checksum_file = metadata_database.backup_folder_path / f"{metadata_database.db_name}_{timestamp}_checksum.sha256"
        checksum_file.write_text("dummy_checksum  dummy_file.txt\n")

        # Mock the open function to raise an error
        mocker.patch("builtins.open", side_effect=Exception("Mocked error"))

        with pytest.raises(RuntimeError) as exc_info:
            metadata_database.verify_checksum_file()

        assert "Failed to verify checksum file" in str(exc_info.value)
        assert "Error verifying checksum file: Mocked error" in caplog.text
