# tests/databses/mysql/test_mysql_restore.py
import pytest
from databases.mysql.mysql_restore import MySQLRestore
from databases.mysql.mysql_utils import MySQLUtils
import mysql.connector


class TestMySQLRestore:
    """ """

    @pytest.fixture
    def live_database(self, mysql_port, monkeypatch):
        """
        Fixture to create a live MySQL database for testing.
        """
        connection = mysql.connector.connect(
            host="localhost",
            user="test_user",
            password="test_password",
            database="test_db",
            port=mysql_port,
        )

        yield connection
        # Cleanup after tests
        connection.cursor().execute("DROP DATABASE IF EXISTS test_db;")
        connection.cursor().execute("CREATE DATABASE test_db;")
        connection.commit()
        connection.close()

    @pytest.fixture
    def setup_method(self, mocker):
        """
        Fixture to provide a mock configuration for the MySQL database.
        """
        mocker.patch.object(
            MySQLUtils,
            "convert_mysql_file_to_statments",
            return_value=[
                "CREATE TABLE test (id INT)",
                "INSERT INTO test (id) VALUES (1);",
            ],
        )

    def test_restore_file_with_valid_file(self, mocker, setup_method, tmp_path):
        """
        Test restoring a MySQL database from a valid SQL file.
        """
        valid_file = tmp_path / "valid.sql"
        valid_file.write_text(
            "CREATE TABLE test (id INT); INSERT INTO test (id) VALUES (1);"
        )

        restore = MySQLRestore(db_name="test_db")
        mock_execute = mocker.patch.object(restore, "execute_with_conflict_handling")
        mock_cursor = mocker.Mock()

        restore.restore_file(mock_cursor, str(valid_file))
        expected_calls = [
            mocker.call(mock_cursor, "CREATE TABLE test (id INT)"),
            mocker.call(mock_cursor, "INSERT INTO test (id) VALUES (1);"),
        ]
        mock_execute.assert_has_calls(expected_calls)
        assert mock_execute.call_count == 2

    def test_restore_file_with_invalid_file(self, mocker, setup_method, tmp_path):
        """
        Test restoring a MySQL database from an invalid SQL file.
        """
        restore = MySQLRestore(db_name="test_db")
        mock_cursor = mocker.Mock()

        with pytest.raises(FileNotFoundError) as exc_info:
            restore.restore_file(mock_cursor, str(None))
        assert f"File {None} does not exist or is not a file." in str(exc_info.value)

    def test_restore_file_with_not_existing_file(self, mocker, setup_method):
        """
        Test restoring a MySQL database from a non-existing SQL file.
        """
        restore = MySQLRestore(db_name="test_db")
        mock_cursor = mocker.Mock()

        with pytest.raises(FileNotFoundError) as exc_info:
            restore.restore_file(mock_cursor, "non_existing_file.sql")
        assert "File non_existing_file.sql does not exist or is not a file." in str(
            exc_info.value
        )

    def test_restore_file_with_not_a_file(self, mocker, setup_method, tmp_path):
        """
        Test restoring a MySQL database from a path that is not a file.
        """
        not_a_file = tmp_path / "not_a_file"
        not_a_file.mkdir()

        restore = MySQLRestore(db_name="test_db")
        mock_cursor = mocker.Mock()

        with pytest.raises(FileNotFoundError) as exc_info:
            restore.restore_file(mock_cursor, str(not_a_file))
        assert f"File {not_a_file} does not exist or is not a file." in str(
            exc_info.value
        )

    def test_restore_statement(self, mocker, setup_method):
        """
        Test restoring a MySQL database from a SQL statement.
        """
        restore = MySQLRestore(db_name="test_db")
        mock_cursor = mocker.Mock()
        mock_execute = mocker.patch.object(restore, "execute_with_conflict_handling")

        restore.restore_statement(mock_cursor, "CREATE TABLE test (id INT);")
        mock_execute.assert_called_once_with(mock_cursor, "CREATE TABLE test (id INT);")

    @pytest.mark.usefixtures("require_mysql")
    def test_execute_with_conflict_handling(self, live_database, mocker):
        """
        Test executing a SQL statement with conflict handling.
        """
        restore = MySQLRestore(db_name="test_db")
        connection = live_database
        cursor = connection.cursor()

        # Actually execute the method (do NOT mock it)
        restore.execute_with_conflict_handling(
            cursor, "CREATE DATABASE IF NOT EXISTS test_db;"
        )
        restore.execute_with_conflict_handling(cursor, "CREATE TABLE test (id INT);")
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        assert ("test",) in tables

    def test_execute_with_conflict_handling_skip(self, mocker, setup_method, caplog):
        """
        Test executing a SQL statement with conflict handling in 'skip' mode.
        """
        restore = MySQLRestore(db_name="test_db", conflict="skip")
        mock_cursor = mocker.Mock()
        mock_cursor = mocker.Mock()
        mock_cursor.execute.side_effect = mysql.connector.Error("Duplicate entry")
        restore.execute_with_conflict_handling(
            mock_cursor, "CREATE TABLE test (id INT);"
        )
        assert "Conflict occurred:" in caplog.text

    def test_execute_with_conflict_handling_abort(self, mocker, setup_method, caplog):
        """
        Test executing a SQL statement with conflict handling in 'abort' mode.
        """
        restore = MySQLRestore(db_name="test_db", conflict="abort")
        mock_cursor = mocker.Mock()
        mock_cursor.execute.side_effect = mysql.connector.Error("Duplicate entry")
        with pytest.raises(mysql.connector.Error) as exc_info:
            restore.execute_with_conflict_handling(
                mock_cursor, "CREATE TABLE test (id INT);"
            )
        assert (
            f"Conflict occurred: {exc_info.value}. Aborting operation." in caplog.text
        )
        assert "Duplicate entry" in str(exc_info.value)

    def test_execute_with_conflict_handling_failure(self, mocker, setup_method):
        """
        Test executing a SQL statement with an unknown conflict handling mode.
        """
        restore = MySQLRestore(db_name="test_db", conflict="unknown")
        mock_cursor = mocker.Mock()
        mock_cursor.execute.side_effect = mysql.connector.Error("Duplicate entry")
        with pytest.raises(ValueError) as exc_info:
            restore.execute_with_conflict_handling(
                mock_cursor, "CREATE TABLE test (id INT);"
            )
        assert "Unknown conflict handling mode: unknown" in str(exc_info.value)
