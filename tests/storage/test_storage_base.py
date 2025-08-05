# tests/storage/test_storage_base.py
import pytest
from storage.storage_base import StorageBase
from pathlib import Path


class MockStorage(StorageBase):
    """
    Mock implementation of StorageBase for testing purposes.
    """

    def upload(self, file_path: Path) -> Path:
        """
        Mock upload method.
        """
        return super().upload(file_path)

    def download(self, file_path: Path) -> Path:
        """
        Mock download method.
        """
        return super().download(file_path)

    def validate_credentials(self) -> bool:
        """
        Mock validate credentials method.
        """
        return super().validate_credentials()

    def delete(self, file_path):
        """
        Mock delete method.
        """
        return super().delete(file_path)


class TestStorageBase:
    """
    Tests for the StorageBase class.
    """

    @pytest.fixture
    def mock_storage(self):
        """
        Create a mock storage instance for testing.
        """
        return MockStorage()

    def test_valid_initialization(self, mock_storage):
        """
        Test that the StorageBase initializes correctly with a valid config.
        """
        assert mock_storage.logger is not None
        assert mock_storage.db_name == "backy_db"

    def test_upload_method(self, mock_storage, caplog):
        """
        Test that the upload method returns the expected path.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            mock_storage.upload(Path("/fake/file"))
        assert "Upload method not implemented in MockStorage" in str(excinfo.value)
        assert "Upload method not implemented in MockStorage" in caplog.text

    def test_download_method(self, mock_storage, caplog):
        """
        Test that the download method returns the expected path.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            mock_storage.download(Path("/fake/file"))
        assert "Download method not implemented in MockStorage" in str(excinfo.value)
        assert "Download method not implemented in MockStorage" in caplog.text

    def test_validate_credentials_method(self, mock_storage, caplog):
        """
        Test that the validate_credentials method returns True.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            mock_storage.validate_credentials()
        assert "Validate credentials method not implemented in MockStorage" in str(
            excinfo.value
        )
        assert (
            "Validate credentials method not implemented in MockStorage" in caplog.text
        )

    def test_delete_method(self, mock_storage, caplog):
        """Test that the delete method returns the expected path."""
        with pytest.raises(NotImplementedError) as excinfo:
            mock_storage.delete(Path("/fake/file"))
        assert "Delete method not implemented in MockStorage" in str(excinfo.value)
        assert "Delete method not implemented in MockStorage" in caplog.text

    def test_generate_dest_path(self, mock_storage):
        """
        Test that the generate_dest_path method returns a valid path.
        """
        file_path = Path("/fake/file")
        dest_path = mock_storage.generate_dest_path(file_path)
        assert dest_path == f"backy_backups/{mock_storage.db_name}/{file_path.name}"

    def test_generate_dest_path_with_spaces_in_db_name(self, mock_storage):
        """
        Test that the generate_dest_path method handles spaces in db_name correctly.
        """
        mock_storage.db_name = "My Database"
        file_path = Path("/fake/file")
        dest_path = mock_storage.generate_dest_path(file_path)
        assert dest_path == "backy_backups/my_database/file"

    def test_generate_dest_path_with_spaces_in_filename(self, mock_storage):
        """
        Test that the generate_dest_path method handles spaces in filename correctly.
        """
        mock_storage.db_name = "MyDatabase"
        file_path = Path("/fake/my file.txt")
        dest_path = mock_storage.generate_dest_path(file_path)
        assert dest_path == "backy_backups/mydatabase/my_file.txt"

    def test_generate_dest_path_with_uppercase_db_name(self, mock_storage):
        """
        Test that the generate_dest_path method handles uppercase db_name correctly.
        """
        mock_storage.db_name = "MyDatabase"
        file_path = Path("/fake/file.txt")
        dest_path = mock_storage.generate_dest_path(file_path)
        assert dest_path == "backy_backups/mydatabase/file.txt"

    def test_generate_dest_path_with_uppercase_filename(self, mock_storage):
        """
        Test that the generate_dest_path method handles uppercase filename correctly.
        """
        mock_storage.db_name = "MyDatabase"
        file_path = Path("/fake/MyFile.TXT")
        dest_path = mock_storage.generate_dest_path(file_path)
        assert dest_path == "backy_backups/mydatabase/myfile.txt"
