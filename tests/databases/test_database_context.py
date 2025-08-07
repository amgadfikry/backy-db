# tests/databases/test_database_base.py
import pytest
from databases.database_context import DatabaseContext
from pathlib import Path
import os


class TestDatabaseContext:
    """
    Test suite for the DatabaseContext class.
    """

    @pytest.fixture
    def setup(self, monkeypatch):
        """
        Fixture to provide a mock configuration for the database.
        """
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        config = {
            "db_name": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
        }
        mock_database = DatabaseContext(config)
        return mock_database

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
        assert mock_database.backup_folder_path == Path(os.getenv("MAIN_BACKUP_PATH"))
        assert mock_database.multiple_files is False
