# tests/io_engine/test_io_creator.py
import pytest
from io_engine.io_creator import IOCreator
from pathlib import Path
import os
import platform


class TestIOCreator:
    """
    Test suite for the IOCreator class.
    This class tests the file creation functionality of the IOCreator.
    """

    @pytest.fixture
    def io_creator(self, mocker, tmp_path):
        """
        Fixture to create an instance of IOCreator for testing.
        This fixture will be used in all test methods.
        """
        mocker.patch.object(
            IOCreator, "_generate_main_backup_path", return_value=tmp_path
        )
        return IOCreator(backup_type="backy", db_name="test_db")

    def test_initialization_with_valid_backup_type(self, io_creator):
        """
        Test that IOCreator initializes correctly with a valid backup type.
        """
        assert io_creator.backup_type == "backy"
        assert io_creator.db_name == "test_db"
        assert io_creator.processing_path is not None
        assert io_creator.timestamp is not None
        assert isinstance(io_creator.processing_path, Path)
        assert io_creator.processing_path.is_dir()
        assert isinstance(io_creator.timestamp, str)

    def test_initialization_with_invalid_backup_type(self):
        """
        Test that IOCreator raises ValueError for an invalid backup type.
        """
        with pytest.raises(ValueError) as exc_info:
            IOCreator(backup_type="invalid_type", db_name="test_db")
        assert "Invalid backup type. Must be 'backy' or 'sql'." in str(exc_info.value)

    def test_create_file_success(self, io_creator, mocker):
        """
        Test the successful creation of a file.
        This test checks if the create_file method works as expected.
        """
        feature_name = "test_feature"
        helper_mock = mocker.patch.object(
            io_creator,
            "_create_file_helper",
            return_value=Path("test_db_test_feature.backy"),
        )
        file_path = io_creator.create_file(feature_name)
        print(file_path)
        print(io_creator.processing_path)
        assert file_path is not None
        assert file_path.name.startswith("test_db_test_feature")
        assert file_path.suffix == ".backy"
        helper_mock.assert_called_once_with(feature_name, io_creator.backup_type)

    def test_create_file_helper_success_with_sql_extension(self, io_creator):
        """
        Test the successful creation of a SQL file using the _create_file_helper method.
        This test checks if the method works correctly for SQL files.
        """
        feature_name = "tables"
        file_path = io_creator._create_file_helper(feature_name, "sql")
        assert file_path is not None
        assert file_path.name.startswith("test_db_tables")
        assert file_path.name.endswith("_backup.sql")
        assert file_path.suffix == ".sql"
        assert file_path.exists()

    def test_create_file_helper_success_with_backy_extension(self, io_creator):
        """
        Test the successful creation of a Backy file using the _create_file_helper method.
        This test checks if the method works correctly for Backy files.
        """
        feature_name = "backup"
        file_path = io_creator._create_file_helper(feature_name, "backy")
        assert file_path is not None
        assert file_path.name.startswith("test_db_backup")
        assert file_path.name.endswith("_backup.backy")
        assert file_path.suffix == ".backy"
        assert file_path.exists()

    def test_create_file_helper_error_handling(self, io_creator, mocker):
        """
        Test that _create_file_helper raises RuntimeError on failure.
        This test checks if the method handles exceptions correctly.
        """
        feature_name = "error_feature"
        mocker.patch(
            "io_engine.io_creator.Path.touch",
            side_effect=Exception("File creation error"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            io_creator._create_file_helper(feature_name, "backy")
        assert "Failed to create BACKY file" in str(exc_info.value)

    @pytest.mark.parametrize(
        "system_name,expected_parts",
        [
            ("Linux", [".local", "share"]),
            ("Darwin", ["Library", "Application Support"]),
            ("Windows", ["AppData", "Roaming"]),
        ],
    )
    def test_os_generate_main_backup_path_default(
        self, expected_parts, system_name, mocker, monkeypatch, tmp_path
    ):
        mocker.patch.dict(os.environ, {})
        monkeypatch.setattr(platform, "system", lambda: system_name)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        io_creator = IOCreator(backup_type="backy", db_name="test_db")
        assert io_creator.processing_path.is_dir()
        print(f"Generated backup path: {io_creator.processing_path}")
        print(os.environ["MAIN_BACKUP_PATH"])
        assert os.environ["MAIN_BACKUP_PATH"] == str(io_creator.processing_path)
        for part in expected_parts:
            assert part in str(io_creator.processing_path)
        assert io_creator.processing_path.exists()
        assert "backy" in str(io_creator.processing_path)
        assert "test_db" in str(io_creator.processing_path)
        full_path = (
            tmp_path
            / "/".join(expected_parts)
            / "backy"
            / f"test_db_{io_creator.timestamp}"
        )
        assert io_creator.processing_path == full_path
