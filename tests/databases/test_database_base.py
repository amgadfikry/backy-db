# tests/databases/test_database_base.py
import pytest
from databases.database_base import DatabaseBase
from typing import Iterator, Tuple


class MockDatabaseBase(DatabaseBase):
    """
    Mock implementation of the DatabaseBase class for testing purposes.
    """

    def connect(self):
        """Connect to the database using the provided configuration."""
        return super().connect()

    def backup(self) -> Iterator[Tuple[str, str]]:
        """Perform a backup of the database."""
        return super().backup()

    def restore(self, feature_data: Tuple[str, str]) -> None:
        """Restore the database from a backup file or files."""
        return super().restore(feature_data)

    def close(self) -> None:
        """Close the database connection."""
        return super().close()


class TestDatabaseBase:
    """
    Test suite for the DatabaseBase class.
    """

    @pytest.fixture
    def setup(self):
        """
        Fixture to provide a mock configuration for the database.
        """
        config = {
            "db_name": "test_db",
            "user": "test_user",
            "password": "test_password",
            "host": "localhost",
            "port": 5432,
        }
        mock_database = MockDatabaseBase(config)
        return mock_database

    @pytest.mark.parametrize("method_name", ["connect", "backup", "restore", "close"])
    def test_abstracted_methods(self, setup, method_name):
        """
        Test that abstract methods raise NotImplementedError with the correct message.
        """
        mock_database = setup
        with pytest.raises(NotImplementedError) as exc_info:
            method = getattr(mock_database, method_name)
            if method_name == "restore":
                method(("dummy_feature", "dummy_statement"))
            else:
                method()
        assert str(exc_info.value) == "Subclasses must implement this method."
