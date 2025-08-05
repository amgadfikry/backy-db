# tests/storage/test_storage_manager.py
import pytest
from storage.storage_manager import StorageManager
from storage.local_storage import LocalStorage


class TestStorageManager:
    """
    Tests for the StorageManager class.
    """

    @pytest.fixture
    def storage_manager_setup(self, monkeypatch):
        """
        Setup fixture for StorageManager tests.
        """
        # Mock LocalStorage to prevent actual file operations during StorageManager tests
        monkeypatch.setattr(LocalStorage, "__init__", lambda self, config: None)
        monkeypatch.setattr(
            LocalStorage, "upload", lambda self, file_path: "/mock/uploaded/path"
        )
        monkeypatch.setattr(
            LocalStorage, "download", lambda self, file_path: "/mock/downloaded/path"
        )
        monkeypatch.setattr(LocalStorage, "validate_credentials", lambda self: True)
        monkeypatch.setattr(LocalStorage, "delete", lambda self, file_path: None)

    def test_init_success_local_storage_with_local_type(self, mocker):
        """
        Test that StorageManager initializes successfully with a supported storage type (local).
        """
        config = {"storage_type": "local", "db_name": "test_db"}
        mocker.patch("storage.storage_manager.LocalStorage", return_value=LocalStorage)
        manager = StorageManager(config)
        assert isinstance(manager.storage, LocalStorage)
        assert manager.storage.logger is not None

    def test_init_unsupported_storage_type(self, caplog):
        """
        Test that StorageManager raises ValueError for an unsupported storage type.
        """
        config = {"storage_type": "unsupported", "db_name": "test_db"}
        with pytest.raises(ValueError) as excinfo:
            StorageManager(config)
        assert "Unsupported storage type: unsupported" in str(excinfo.value)
        assert "Unsupported storage type: unsupported" in caplog.text

    def test_upload_success(self, storage_manager_setup):
        """
        Test that the upload method of StorageManager calls the underlying storage's upload method.
        """
        config = {"storage_type": "local", "db_name": "test_db"}
        manager = StorageManager(config)
        uploaded_path = manager.upload("/path/to/file.txt")
        assert uploaded_path == "/mock/uploaded/path"

    def test_download_success(self, storage_manager_setup):
        """
        Test that the download method of StorageManager calls the underlying storage's download method.
        """
        config = {"storage_type": "local", "path": "/tmp/test_storage"}
        manager = StorageManager(config)
        downloaded_path = manager.download("/path/to/file.txt")
        assert downloaded_path == "/mock/downloaded/path"

    def test_validate_credentials_success(self, storage_manager_setup):
        """
        Test that the validate_credentials method of StorageManager calls the underlying storage's validate_credentials method.
        """
        config = {"storage_type": "local", "db_name": "test_db"}
        manager = StorageManager(config)
        result = manager.storage.validate_credentials()
        assert result is True

    def test_delete_success(self, storage_manager_setup):
        """
        Test that the delete method of StorageManager calls the underlying storage's delete method.
        """
        config = {"storage_type": "local", "db_name": "test_db"}
        manager = StorageManager(config)
        # Mocking delete method to avoid actual file deletion
        assert manager.delete("/path/to/file.txt") is None
