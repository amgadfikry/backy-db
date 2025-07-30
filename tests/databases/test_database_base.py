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
