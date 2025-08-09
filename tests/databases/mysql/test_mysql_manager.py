# tests/databases/test_mysql_manager.py
import pytest
from databases.mysql.mysql_manager import MySQLManager


class TestMySQLManager:
    """
    Test suite for MySQL database operations.
    """

    @pytest.fixture
    def live_mysql(self, mysql_port, monkeypatch):
        """
        Fixture to provide a live MySQL database connection.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        db_config = {
            "host": "localhost",
            "port": mysql_port,
            "user": "test_user",
            "db_name": "test_db",
        }
        return MySQLManager(db_config)

    @pytest.fixture
    def setup_method(self, mocker, monkeypatch):
        """
        Fixture to provide a mock configuration for the database.
        """
        mock_streaming = mocker.Mock()
        mocker.patch(
            "databases.mysql.mysql_streaming.MySQLStreaming",
            return_value=mock_streaming,
        )
        mock_restore = mocker.Mock()
        mocker.patch(
            "databases.mysql.mysql_restore.MySQLRestore",
            return_value=mock_restore,
        )
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        db_config = {
            "host": "localhost",
            "port": 3333,
            "user": "test_user",
            "db_name": "test_db",
        }
        db = MySQLManager(db_config)
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        return db

    def test_initialization(self, setup_method):
        """
        Test to ensure that the MySQLManager is initialized correctly.
        """
        db = setup_method
        assert db.host == "localhost"
        assert db.user == "test_user"
        assert db.password == "test_password"
        assert db.db_name == "test_db"
        assert db.features == {
            "tables": False,
            "data": False,
            "views": False,
            "functions": False,
            "procedures": False,
            "triggers": False,
            "events": False,
        }
        assert db.version == "Unknown"
        assert db.streaming is not None
        assert db.restoring is not None
        assert db.restore_mode is None
        assert db.conflict_mode == "skip"

    @pytest.mark.usefixtures("require_mysql")
    def test_connection_success(self, live_mysql):
        """
        Test to ensure that the MySQL database connection is successful.
        """
        db = live_mysql
        db.connect()
        assert db.connection is not None
        assert db.version is not None

    @pytest.mark.usefixtures("require_mysql")
    def test_connection_failure(self, mocker, live_mysql, caplog):
        """
        Ensure the MySQL database connection fails with invalid credentials.
        """
        mocker.patch(
            "mysql.connector.connect", side_effect=Exception("Connection failed")
        )

        with pytest.raises(ConnectionError) as exc_info:
            live_mysql.connect()
        assert live_mysql.connection is None
        assert live_mysql.version == "Unknown"
        assert "Failed to connect to MySQL database: Connection failed" in str(
            exc_info.value
        )
        assert "Failed to connect to MySQL database: Connection failed" in caplog.text

    def test_backup_successfully_one_file(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database backup is created successfully.
        """
        db = setup_method
        db.features["tables"] = True
        db.features["data"] = True
        db.features["views"] = True
        mocker.patch(
            "databases.mysql.mysql_utils.MySQLUtils.create_mysql_file_opening",
            return_value="test\n",
        )
        mocker.patch.object(
            db.streaming, "stream_tables_statements", return_value=["CREATE TABLE"]
        )
        mocker.patch.object(
            db.streaming, "stream_data_statements", return_value=["INSERT INTO"]
        )
        mocker.patch.object(
            db.streaming, "stream_views_statements", return_value=["CREATE VIEW"]
        )
        function_mocker = mocker.patch.object(
            db.streaming,
            "stream_functions_statements",
            return_value=["CREATE FUNCTION"],
        )
        backups = list(db.backup())
        assert isinstance(backups, list)
        assert len(backups) == 5
        assert backups[0][0] == "full"
        assert backups[0][1].startswith("CREATE DATABASE IF NOT EXISTS")
        assert backups[1][0] == "full"
        assert backups[1][1].startswith("USE")
        assert backups[2][0] == "full"
        assert backups[2][1].startswith("CREATE TABLE")
        assert backups[3][0] == "full"
        assert backups[3][1].startswith("INSERT INTO")
        assert backups[4][0] == "full"
        assert backups[4][1].startswith("CREATE VIEW")
        assert not function_mocker.called

    def test_backup_successfully_multiple_files(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database backup is created successfully with multiple files.
        """
        db = setup_method
        db.multiple_files = True
        db.features["tables"] = True
        db.features["data"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        mocker.patch(
            "databases.mysql.mysql_utils.MySQLUtils.create_mysql_file_opening",
            return_value="test\n",
        )
        mocker.patch.object(
            db.streaming, "stream_tables_statements", return_value=["CREATE TABLE"]
        )
        mocker.patch.object(
            db.streaming, "stream_data_statements", return_value=["INSERT INTO"]
        )
        backups = list(db.backup())
        assert isinstance(backups, list)
        assert len(backups) == 6
        assert backups[0][0] == "tables"
        assert backups[0][1].startswith("CREATE DATABASE IF NOT EXISTS")
        assert backups[1][0] == "tables"
        assert backups[1][1].startswith("USE")
        assert backups[2][0] == "tables"
        assert backups[2][1].startswith("CREATE TABLE")
        assert backups[3][0] == "data"
        assert backups[3][1].startswith("CREATE DATABASE IF NOT EXISTS")
        assert backups[4][0] == "data"
        assert backups[4][1].startswith("USE")
        assert backups[5][0] == "data"
        assert backups[5][1].startswith("INSERT INTO")

    def test_backup_empty_database(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database backup is created successfully.
        """
        db = setup_method
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        mocker.patch(
            "databases.mysql.mysql_utils.MySQLUtils.create_mysql_file_opening",
            return_value="test\n",
        )
        backups = list(db.backup())
        assert isinstance(backups, list)
        assert len(backups) == 2
        assert backups[0][0] == "full"
        assert backups[0][1].startswith("CREATE DATABASE IF NOT EXISTS")
        assert backups[1][0] == "full"
        assert backups[1][1].startswith("USE")

    def test_backup_failure(self, setup_method, mocker, caplog):
        """
        Ensure that an error is raised when the backup process fails.
        """
        db = setup_method
        db.features["tables"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        mocker.patch(
            "databases.mysql.mysql_utils.MySQLUtils.create_mysql_file_opening",
            return_value="test\n",
        )
        mocker.patch.object(
            db.streaming, "stream_tables_statements", side_effect=Exception
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.backup())
        assert "Error during getting tables backup:" in str(exc_info.value)

    def test_restore_success_mode_sql(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database restore is successful with sql mode.
        """
        db = setup_method
        db.restore_mode = "sql"
        db.features["tables"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        restore_mock = mocker.patch.object(
            db.restoring, "restore_file", return_value=None
        )
        feature_data = ("tables", "SQL statement 1")
        db.restore(feature_data)
        restore_mock.assert_called_once()

    def test_restore_success_mode_backy(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database restore is successful with backy mode.
        """
        db = setup_method
        db.restore_mode = "backy"
        db.features["tables"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        restore_mock = mocker.patch.object(
            db.restoring, "restore_statement", return_value=None
        )
        feature_data = ("tables", "SQL statement 1")
        db.restore(feature_data)
        restore_mock.assert_called_once()

    def test_restore_skip_inactive_feature(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database restore skips inactive features.
        """
        db = setup_method
        db.restore_mode = "backy"
        db.features["tables"] = False
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        restore_mock = mocker.patch.object(
            db.restoring, "restore_statement", return_value=None
        )
        feature_data = ("tables", "SQL statement 1")
        db.restore(feature_data)
        restore_mock.assert_not_called()

    def test_restore_failure(self, setup_method, mocker):
        """
        Ensure that an error is raised when the restore process fails.
        """
        db = setup_method
        db.restore_mode = "backy"
        db.features["tables"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        mocker.patch.object(
            db.restoring, "restore_statement", side_effect=Exception("Restore failed")
        )
        feature_data = ("tables", "SQL statement 1")
        with pytest.raises(RuntimeError) as exc_info:
            db.restore(feature_data)
        assert "Error during restoring tables backup" in str(exc_info.value)

    def test_restore_not_supported_mode(self, setup_method, mocker):
        """
        Ensure that a NotImplementedError is raised for unsupported restore modes.
        """
        db = setup_method
        db.restore_mode = "unsupported_mode"
        db.features["tables"] = True
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        feature_data = ("tables", "SQL statement 1")
        with pytest.raises(NotImplementedError) as exc_info:
            db.restore(feature_data)
        assert (
            "Restore mode 'unsupported_mode' is not implemented for MySQLDatabase"
            in str(exc_info.value)
        )

    def test_restore_if_feature_is_full(self, setup_method, mocker):
        """
        Test to ensure that the MySQL database restore works correctly when the feature is 'full'.
        """
        db = setup_method
        db.restore_mode = "backy"
        mocker.patch.object(db, "connection", mocker.Mock())
        mocker.patch.object(db.connection, "cursor", return_value=mocker.Mock())
        restore_mock = mocker.patch.object(
            db.restoring, "restore_statement", return_value=None
        )
        feature_data = ("full", "SQL statement 1")
        db.restore(feature_data)
        restore_mock.assert_called_once()

    @pytest.mark.usefixtures("require_mysql")
    def test_close_connection_successfully(self, live_mysql):
        """
        Test to ensure that the MySQL database connection is closed successfully.
        """
        db = live_mysql
        db.connect()
        assert db.connection is not None
        db.close()
        assert db.connection is None

    @pytest.mark.usefixtures("require_mysql")
    def test_close_connection_no_active_connection(self, live_mysql, caplog):
        """
        Test to ensure that closing the MySQL database connection when no active connection exists
        does not raise an error.
        """
        db = live_mysql
        db.close()
        assert db.connection is None
        assert "No active MySQL database connection to close." in caplog.text
