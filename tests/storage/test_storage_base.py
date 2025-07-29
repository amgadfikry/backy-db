# tests/storage/test_storage_base.py
import pytest
from storage.storage_base import StorageBase
from pathlib import Path
import shutil


class MockStorage(StorageBase):
    """
    Mock implementation of StorageBase for testing purposes.
    """

    def upload(self) -> Path:
        """
        Mock upload method.
        """
        return super().upload()

    def download(self) -> Path:
        """
        Mock download method.
        """
        return super().download()


class TestStorageBase:
    """
    Tests for the StorageBase class.
    """

    @pytest.fixture
    def mock_storage(self, tmp_path, monkeypatch):
        """
        Create a mock storage instance for testing.
        """
        storage_path = tmp_path / "mock" / "path"
        storage_path.mkdir(parents=True, exist_ok=True)
        processed_path = tmp_path / "processed"
        processed_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(processed_path))
        storage = MockStorage(
            config={"storage_type": "local", "path": str(storage_path)}
        )
        yield storage
        shutil.rmtree(storage_path, ignore_errors=True)
        shutil.rmtree(processed_path, ignore_errors=True)

    def test_valid_initialization(self, mock_storage):
        """
        Test that the StorageBase initializes correctly with a valid config.
        """
        assert mock_storage.storage_type == "local"
        assert mock_storage.path.name == "path"
        assert mock_storage.processed_path.exists()
        assert mock_storage.logger is not None

    def test_invalid_storage_path(self, caplog):
        """
        Test that StorageBase raises ValueError when the storage path does not exist.
        """
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                MockStorage(config={"storage_type": "local", "path": "/invalid/path"})
            assert "Storage path is not set or does not exist." in str(excinfo.value)
            assert "Storage path is not set or does not exist." in caplog.text

    def test_invalid_main_backup_path(self, tmp_path, caplog, monkeypatch):
        """
        Test that StorageBase raises ValueError when MAIN_BACKUP_PATH is not set.
        """
        storage_path = tmp_path / "mock" / "path"
        storage_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("MAIN_BACKUP_PATH", None)
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                MockStorage(config={"storage_type": "local", "path": str(storage_path)})
            assert "MAIN_BACKUP_PATH environment variable is not set." in str(
                excinfo.value
            )
            assert "MAIN_BACKUP_PATH environment variable is not set." in caplog.text

    def test_upload_method(self, mock_storage, caplog):
        """
        Test that the upload method returns the expected path.
        """
        with caplog.at_level("ERROR"):
            with pytest.raises(NotImplementedError) as excinfo:
                mock_storage.upload()
            assert "Upload method not implemented in MockStorage" in str(excinfo.value)
            assert "Upload method not implemented in MockStorage" in caplog.text

    def test_download_method(self, mock_storage, caplog):
        """
        Test that the download method returns the expected path.
        """
        with caplog.at_level("ERROR"):
            with pytest.raises(NotImplementedError) as excinfo:
                mock_storage.download()
            assert "Download method not implemented in MockStorage" in str(
                excinfo.value
            )
            assert "Download method not implemented in MockStorage" in caplog.text
