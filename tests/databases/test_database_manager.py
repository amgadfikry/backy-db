# tests/databases/test_database_manager.py
from databases.database_manager import DatabaseManager
import pytest


class TestDatabaseManager:
    """
    Test suite for the DatabaseManager class.
    This class tests the backup functionality of the DatabaseManager.
    """

    @pytest.fixture
    def setup_method(self):
        """
        Fixture to provide a mock configuration for the database.
        """
        config = {
            "db_type": "mysql",
            "db_name": "test_db",
            "user": "test_user",
            "host": "localhost",
            "port": 5432,
        }
        return config

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

    def test_calling_with_statement(self, setup_method, mocker):
        """
        Test to ensure that the DatabaseManager can be used in a 'with' statement.
        """
        config = setup_method
        mock_db = mocker.Mock()
        manager = DatabaseManager(config)
        manager.db = mock_db
        with manager as m:
            mock_db.connect.assert_called_once()
            assert m is manager

    def test_exit_method(self, setup_method, mocker):
        """
        Test to ensure that the exit method closes the database connection.
        """
        config = setup_method
        mock_db = mocker.Mock()
        manager = DatabaseManager(config)
        manager.db = mock_db
        with manager:
            pass
        mock_db.close.assert_called_once()

    def test_connect_method(self, setup_method, mocker, monkeypatch):
        """
        Test to ensure that the connect method establishes a connection to the database.
        """
        config = setup_method
        mysql_mocker = mocker.Mock()
        mysql_mocker.connect = mocker.Mock()
        mysql_mocker.connection = mocker.Mock()
        mysql_mocker.connection.start_transaction = mocker.Mock()
        monkeypatch.setitem(
            DatabaseManager.DATABASES, "mysql", lambda config: mysql_mocker
        )
        db_manager = DatabaseManager(config)
        db_manager.connect()
        assert mysql_mocker.connect.called
        assert mysql_mocker.connection.start_transaction.called

    def test_close_method(self, setup_method, mocker, monkeypatch):
        """
        Test to ensure that the close method closes the database connection.
        """
        config = setup_method
        mysql_mocker = mocker.Mock()
        mysql_mocker.connect = mocker.Mock()
        mysql_mocker.connection = mocker.Mock()
        mysql_mocker.connection.commit = mocker.Mock()
        monkeypatch.setitem(
            DatabaseManager.DATABASES, "mysql", lambda config: mysql_mocker
        )
        db_manager = DatabaseManager(config)
        db_manager.close()
        assert mysql_mocker.connection.commit.called
        assert mysql_mocker.close.called

    def test_backup_process_success(self, setup_method, mocker):
        """
        Test to ensure that the backup process completes successfully.
        """
        config = setup_method
        db_manager = DatabaseManager(config)

        # Mock the database and backup methods
        mocker.patch.object(
            db_manager.db,
            "backup",
            return_value=[
                ("feature1", "SQL statement 1"),
                ("feature2", "SQL statement 2"),
            ],
        )
        backups = list(db_manager.backup())
        assert isinstance(backups, list)
        assert len(backups) == 2
        assert backups[0][0] == "feature1"
        assert backups[0][1] == "SQL statement 1"
        assert backups[1][0] == "feature2"
        assert backups[1][1] == "SQL statement 2"
        # Verify that the database methods were called
        assert db_manager.db.backup.called

    def test_backup_process_backup_failure(self, setup_method, mocker, caplog):
        """
        Test to ensure that the backup process raises an error when the backup fails.
        """
        config = setup_method
        db_manager = DatabaseManager(config)

        # Mock the database
        mocker.patch.object(
            db_manager.db,
            "backup",
            side_effect=RuntimeError("No backup files were created."),
        )

        with pytest.raises(RuntimeError) as exc_info:
            list(db_manager.backup())
        assert (
            str(exc_info.value)
            == "Error during backup process: No backup files were created."
        )
        assert db_manager.db.backup.called
        assert (
            "Error during backup process: No backup files were created." in caplog.text
        )

    def test_restore_process_success(self, setup_method, mocker, monkeypatch):
        """
        Test to ensure that the restore process completes successfully.
        """
        config = setup_method
        mysql_mocker = mocker.Mock()
        mysql_mocker.restore = mocker.Mock()
        mysql_mocker.connect = mocker.Mock()
        mysql_mocker.connection = mocker.Mock()
        mysql_mocker.connection.commit = mocker.Mock()
        monkeypatch.setitem(
            DatabaseManager.DATABASES, "mysql", lambda config: mysql_mocker
        )
        db_manager = DatabaseManager(config)
        # Mock the restore method
        feature_data = ("feature1", "SQL statement 1")
        db_manager.restore(feature_data)
        db_manager.feature = feature_data[0]
        # Verify that the restore method was called with the correct data
        assert mysql_mocker.connection.commit.called
        mysql_mocker.restore.assert_called_once_with(feature_data)

    def test_restore_process_failure(self, setup_method, mocker, caplog, monkeypatch):
        """
        Test to ensure that the restore process raises an error when the restore fails.
        """
        config = setup_method
        mysql_mocker = mocker.Mock()
        mysql_mocker.restore = mocker.Mock(side_effect=RuntimeError("Restore failed."))
        mysql_mocker.connection = mocker.Mock()
        mysql_mocker.connection.commit = mocker.Mock()
        mysql_mocker.connection.rollback = mocker.Mock()
        monkeypatch.setitem(
            DatabaseManager.DATABASES, "mysql", lambda config: mysql_mocker
        )
        db_manager = DatabaseManager(config)
        feature_data = ("feature1", "SQL statement 1")
        with pytest.raises(RuntimeError) as exc_info:
            db_manager.restore(feature_data)
        mysql_mocker.connection.rollback.assert_called_once()
        assert str(exc_info.value) == "Error during restore process: Restore failed."
        assert "Error during restore process: Restore failed." in caplog.text
