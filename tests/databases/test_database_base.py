# tests/databases/test_database_base.py
import shutil
import pytest
import tempfile
from pathlib import Path
from databases.database_base import DatabaseBase


class MockDatabaseBase(DatabaseBase):
    """
    Mock implementation of the DatabaseBase class for testing purposes.
    This class implements the abstract methods with simple pass statements.
    """

    def connect(self):
        return super().connect()

    def backup(self, timestamp: str) -> Path:
        return super().backup(timestamp)

    def restore(self, backup_file: Path):
        return super().restore(backup_file)

    def close(self):
        return super().close()


class TestDatabaseBase:
    """
    Test suite for the DatabaseBase class.
    """

    @pytest.fixture
    def setup(self, monkeypatch):
        """
        Fixture to provide a mock configuration for the database.
        """
        temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("LOGGING_PATH", temp_dir)
        monkeypatch.setenv("MAIN_BACKUP_PATH", (Path(temp_dir) / "backups"))

        config = {
            "db_name": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
        }
        mock_database = MockDatabaseBase(config=config)
        yield mock_database
        # Cleanup after the test
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialization(self, setup):
        """
        Test the initialization of the mock database with the provided configuration.
        """
        mock_database = setup
        assert mock_database.db_name == "test_db"
        assert mock_database.user == "test_user"
        assert mock_database.password == "test_password"
        assert mock_database.host == "localhost"
        assert mock_database.port == 5432
        assert mock_database.connection is None
        assert mock_database.version == "Unknown"

    @pytest.mark.parametrize("method_name", ["connect", "backup", "restore", "close"])
    def test_abstracted_methods(self, setup, method_name):
        """
        Test that abstract methods raise NotImplementedError with the correct message.
        """
        mock_database = setup
        with pytest.raises(NotImplementedError) as exc_info:
            method = getattr(mock_database, method_name)
            if method_name == "backup":
                method("dummy_timestamp")
            elif method_name == "restore":
                method(Path("dummy_backup.sql"))
            else:
                method()
        assert str(exc_info.value) == "Subclasses must implement this method."

    def test_topotopological_sort_success(self, setup):
        """
        Test the topological sort method with a valid dependency graph.
        """
        mock_database = setup
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        sorted_list = mock_database.topological_sort(deps)
        assert sorted_list == ["D", "B", "C", "A"]

    def test_topological_sort_cycle(self, setup, caplog):
        """
        Test the topological sort method with a cyclic dependency graph.
        """
        mock_database = setup
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}
        with pytest.raises(RuntimeError) as exc_info:
            mock_database.topological_sort(deps)
        assert (
            str(exc_info.value)
            == "Cycle detected in dependency graph, cannot perform topological sort."
        )
        assert (
            "Cycle detected in dependency graph, cannot perform topological sort."
            in caplog.text
        )

    def test_topological_sort_empty(self, setup):
        """
        Test the topological sort method with an empty dependency graph.
        """
        mock_database = setup
        deps = {}
        sorted_list = mock_database.topological_sort(deps)
        assert sorted_list == []

    def test_topological_sort_single_node(self, setup):
        """
        Test the topological sort method with a single node dependency graph.
        """
        mock_database = setup
        deps = {"A": []}
        sorted_list = mock_database.topological_sort(deps)
        assert sorted_list == ["A"]

    def test_create_sql_backup_file_success(self, setup):
        """
        Test the create_sql_backup_file method with valid content.
        """
        mock_database = setup
        backup_file = Path("test_backup.sql")
        content = "CREATE TABLE test (id INT);"
        created_file = mock_database.create_sql_backup_file(backup_file, content)
        assert created_file == backup_file
        assert backup_file.exists()
        with open(backup_file, "r") as f:
            file_content = f.read()
        assert "-- Backup for" in file_content
        assert "CREATE DATABASE IF NOT EXISTS" in file_content
        assert "USE" in file_content
        assert content in file_content
        backup_file.unlink()

    def test_create_sql_backup_file_error(self, setup, caplog, mocker):
        """
        Test the create_sql_backup_file method with an error during file creation.
        """
        mock_database = setup
        backup_file = Path("/invalid_path/test_backup.sql")
        content = "CREATE TABLE test (id INT);"

        # Mock the open function to raise an IOError
        mocker.patch("builtins.open", side_effect=IOError("File creation error"))

        with pytest.raises(RuntimeError) as exc_info:
            mock_database.create_sql_backup_file(backup_file, content)

        assert str(exc_info.value) == "Failed to create backup file"
        assert "Error creating backup file" in caplog.text
