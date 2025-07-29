# tests/storage/test_storage_manager.py
import pytest
from storage.storage_manager import StorageManager
from storage.local_storage import LocalStorage
from pathlib import Path
import logging


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
            LocalStorage, "upload", lambda self: Path("/mock/uploaded/path")
        )
        monkeypatch.setattr(
            LocalStorage, "download", lambda self: Path("/mock/downloaded/path")
        )

    def test_init_success_local_storage(self, storage_manager_setup):
        """
        Test that StorageManager initializes successfully with a supported storage type (local).
        """
        config = {"storage_type": "local", "path": "/tmp/test_storage"}
        manager = StorageManager(config)
        assert isinstance(manager.storage, LocalStorage)

    def test_init_unsupported_storage_type(self, caplog):
        """
        Test that StorageManager raises ValueError for an unsupported storage type.
        """
        config = {"storage_type": "unsupported", "path": "/tmp/test_storage"}
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as excinfo:
                StorageManager(config)
            assert "Unsupported storage type: unsupported" in str(excinfo.value)
            assert "Unsupported storage type: unsupported" in caplog.text

    def test_upload_success(self, storage_manager_setup):
        """
        Test that the upload method of StorageManager calls the underlying storage's upload method.
        """
        config = {"storage_type": "local", "path": "/tmp/test_storage"}
        manager = StorageManager(config)
        uploaded_path = manager.upload()
        assert uploaded_path == Path("/mock/uploaded/path")

    def test_download_success(self, storage_manager_setup):
        """
        Test that the download method of StorageManager calls the underlying storage's download method.
        """
        config = {"storage_type": "local", "path": "/tmp/test_storage"}
        manager = StorageManager(config)
        downloaded_path = manager.download()
        assert downloaded_path == Path("/mock/downloaded/path")
