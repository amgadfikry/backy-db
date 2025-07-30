
import pytest
from storage.local_storage import LocalStorage
import shutil


class TestLocalStorage:
    """
    Tests for the LocalStorage class.
    """

    @pytest.fixture
    def local_storage_setup(self, tmp_path, monkeypatch):
        """
        Setup fixture for LocalStorage tests.
        """
        # Create mock directories
        storage_path = tmp_path / "storage"
        storage_path.mkdir()
        processed_path = tmp_path / "process"
        processed_path.mkdir(parents=True)
        # Mock environment variable
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(processed_path))
        storage_config = {"storage_type": "local", "path": str(storage_path)}
        local_storage = LocalStorage(config=storage_config)
        # Return the local storage instance and paths
        yield local_storage, storage_path, processed_path
        # Teardown: remove temporary directories
        shutil.rmtree(tmp_path, ignore_errors=True)

    def test_upload_success(self, local_storage_setup):
        """
        Test that the upload method successfully moves files to the storage path.
        """
        local_storage, storage_path, processed_path = local_storage_setup
        # Create files inside the process path
        processed_path.joinpath("file1.txt").write_text("Test file 1")
        processed_path.joinpath("file2.txt").write_text("Test file 2")
        # Call the upload method
        returned_path = local_storage.upload()
        assert returned_path == storage_path / processed_path.name
        files = {f.name for f in (storage_path / processed_path.name).glob("*")}
        assert len(files) == 2
        assert files == {"file1.txt", "file2.txt"}

    def test_upload_failure(self, local_storage_setup, mocker, caplog):
        """
        Test that the upload method handles exceptions gracefully.
        """
        local_storage, _, _ = local_storage_setup
        # Simulate shutil.copytree raising an exception
        mocker.patch("storage.local_storage.shutil.copytree", side_effect=OSError("Disk full error"))
        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                local_storage.upload()
            assert "Failed to upload file: Disk full error" in str(excinfo.value)
            assert "Failed to upload file: Disk full error" in caplog.text

    def test_download_success(self, local_storage_setup):
        """
        Test that the download method successfully moves files to the processed path.
        """
        local_storage, storage_path, processed_path = local_storage_setup
        # Create files inside the storage path
        storage_path.joinpath("file1.txt").write_text("Test file 1")
        storage_path.joinpath("file2.txt").write_text("Test file 2")
        # Call the download method
        returned_path = local_storage.download()
        assert returned_path == processed_path
        files = {f.name for f in processed_path.glob("*")}
        assert len(files) == 2
        assert files == {"file1.txt", "file2.txt"}

    def test_download_failure(self, local_storage_setup, mocker, caplog):
        """
        Test that the download method handles exceptions gracefully.
        """
        local_storage, _, _ = local_storage_setup
        # Simulate shutil.copytree raising an exception
        mocker.patch("storage.local_storage.shutil.copytree", side_effect=OSError("Network error"))
        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                local_storage.download()
            assert "Failed to download file: Network error" in str(excinfo.value)
            assert "Failed to download file: Network error" in caplog.text
