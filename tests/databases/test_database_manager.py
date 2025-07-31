# tests/databases/test_database_manager.py
from databases.database_manager import DatabaseManager
import tempfile
import shutil
import pytest
from pathlib import Path


class TestDatabaseManager:
    """
    Test suite for the DatabaseManager class.
    This class tests the backup functionality of the DatabaseManager.
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
            "db_type": "mysql",
            "version": "8.0",
            "db_name": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
        }

        yield config
        # Cleanup after tests
        shutil.rmtree(temp_dir)

    def test_if_database_type_is_not_supported(self, setup_method, caplog):
        """
        Test to ensure that an error is raised when an unsupported database type is provided.
        """
        config = setup_method
        config["db_type"] = "invalid_db_type"
        with pytest.raises(ValueError) as exc_info:
            DatabaseManager(config)
        assert str(exc_info.value) == "Unsupported database type: invalid_db_type"
        assert "Unsupported database type: invalid_db_type" in caplog.text

    def test_initialization_with_valid_config(self, setup_method):
        """
        Test to ensure that the DatabaseManager initializes correctly with a valid configuration.
        """
        config = setup_method
        db_manager = DatabaseManager(config)
        assert db_manager.db is not None
        assert db_manager.metadata is not None

    def test_backup_process_success(self, setup_method, mocker):
        """
        Test to ensure that the backup process completes successfully.
        """
        config = setup_method
        db_manager = DatabaseManager(config)

        # Mock the database connection and backup methods
        mocker.patch.object(db_manager.db, "connect", return_value=None)
        mocker.patch.object(db_manager.db, "backup", return_value=["backup_file.sql"])
        mocker.patch.object(
            db_manager.metadata,
            "create_metadata_file",
            return_value=Path("metadata.json"),
        )
        mocker.patch.object(
            db_manager.metadata, "create_backup_folder", return_value=Path("/backup/")
        )
        mocker.patch.object(
            db_manager.metadata,
            "create_checksum_file",
            return_value=Path("checksum.txt"),
        )
        mocker.patch.object(db_manager.db, "close", return_value=None)

        backup_folder = db_manager.backup()
        assert backup_folder == Path("/backup/")
        assert db_manager.db.connect.called
        assert db_manager.db.backup.called
        assert db_manager.metadata.create_metadata_file.called
        assert db_manager.metadata.create_backup_folder.called
        assert db_manager.db.close.called

    def test_backup_process_backup_failure(self, setup_method, mocker, caplog):
        """
        Test to ensure that the backup process raises an error when the database connection fails.
        """
        config = setup_method
        db_manager = DatabaseManager(config)

        # Mock the database
        mocker.patch.object(db_manager.db, "connect", return_value=None)
        mocker.patch.object(db_manager.db, "backup", return_value=None)
        mocker.patch.object(
            db_manager.metadata,
            "create_metadata_file",
            return_value=Path("metadata.json"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            db_manager.backup()
        assert str(exc_info.value) == "No backup files were created."
        assert db_manager.db.connect.called
        assert db_manager.db.backup.called
        assert not db_manager.metadata.create_metadata_file.called
        assert "No backup files were created during the backup process." in caplog.text

    def test_backup_process_general_failure(self, setup_method, mocker, caplog):
        """
        Test to ensure that the backup process raises an error when an unexpected error occurs.
        """
        config = setup_method
        db_manager = DatabaseManager(config)

        # Mock the database connection and backup methods to raise an exception
        mocker.patch.object(
            db_manager.db, "connect", side_effect=RuntimeError("Connection failed")
        )

        with pytest.raises(RuntimeError) as exc_info:
            db_manager.backup()
        assert str(exc_info.value) == "Failed to perform backup: Connection failed"
        assert "Error during backup process: Connection failed" in caplog.text
        assert db_manager.db.connect.called

    def test_restore_process_not_implemented(self, setup_method):
        """
        Test to ensure that the restore method raises a NotImplementedError.
        """
        config = setup_method
        db_manager = DatabaseManager(config)
        with pytest.raises(NotImplementedError) as exc_info:
            db_manager.restore(Path("backup_file.sql"))
        assert (
            str(exc_info.value)
            == "Restore method is not implemented for this database type."
        )
