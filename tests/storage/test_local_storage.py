import pytest
from storage.local_storage import LocalStorage
import os
from pathlib import Path


class TestLocalStorage:
    """
    Tests for the LocalStorage class.
    """

    @pytest.fixture(autouse=True)
    def local_storage_setup(self, tmp_path, monkeypatch):
        """
        Setup fixture for LocalStorage tests.
        """
        # Create a temporary directory for LOCAL_PATH
        local_path = tmp_path / "local_storage"
        local_path.mkdir()
        monkeypatch.setenv("LOCAL_PATH", str(local_path))

    def test_init_success(self):
        """
        Test that LocalStorage initializes successfully with the correct environment variables.
        """
        local_storage = LocalStorage(db_name="test_db")
        assert isinstance(local_storage, LocalStorage)
        assert local_storage.db_name == "test_db"
        assert local_storage.destination_path == os.getenv("LOCAL_PATH")
        assert local_storage.processing_path == os.getenv("MAIN_BACKUP_PATH")
        assert local_storage.logger is not None

    def test_validate_credentials_success(self):
        """
        Test that validate_credentials returns True when LOCAL_PATH is set.
        """
        local_storage = LocalStorage(db_name="test_db")
        assert local_storage.validate_credentials() is True

    def test_validate_credentials_failure_no_destination_path(
        self, monkeypatch, caplog
    ):
        """
        Test that validate_credentials returns False when LOCAL_PATH is not set.
        """
        # Remove LOCAL_PATH to simulate the environment variable not being set
        monkeypatch.delenv("LOCAL_PATH", raising=False)
        local_storage = LocalStorage(db_name="test_db")
        assert local_storage.validate_credentials() is False
        assert "Local storage paths are not set or do not exist." in caplog.text

    def test_validate_credentials_failure_not_exist_destination_path(
        self, monkeypatch, caplog
    ):
        """
        Test that validate_credentials returns False when LOCAL_PATH does not exist.
        """
        # Set LOCAL_PATH to a non-existent path
        monkeypatch.setenv("LOCAL_PATH", "/non/existent/path")
        local_storage = LocalStorage(db_name="test_db")
        assert local_storage.validate_credentials() is False
        assert "Local storage paths are not set or do not exist." in caplog.text

    def test_validate_credentials_failure_no_processing_path(self, monkeypatch, caplog):
        """
        Test that validate_credentials returns False when MAIN_BACKUP_PATH is not set.
        """
        # Remove MAIN_BACKUP_PATH to simulate the environment variable of processing path is not being set
        monkeypatch.delenv("MAIN_BACKUP_PATH", raising=False)
        local_storage = LocalStorage(db_name="test_db")
        assert local_storage.validate_credentials() is False
        assert "Processing path is not set or does not exist." in caplog.text

    def test_validate_credentials_failure_not_exist_processing_path(
        self, monkeypatch, caplog
    ):
        """
        Test that validate_credentials returns False when MAIN_BACKUP_PATH does not exist.
        """
        # Set MAIN_BACKUP_PATH to a non-existent path
        monkeypatch.setenv("MAIN_BACKUP_PATH", "/non/existent/path")
        local_storage = LocalStorage(db_name="test_db")
        assert local_storage.validate_credentials() is False
        assert "Processing path is not set or does not exist." in caplog.text

    def test_upload_success_file(self, tmp_path):
        """
        Test that upload successfully copies a file to the destination path.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Call the upload method and check the result
        uploaded_path = local_storage.upload(str(test_file))
        assert Path(uploaded_path).exists()
        assert Path(uploaded_path).read_text() == "This is a test file."
        assert (
            Path(uploaded_path).parent
            == Path(local_storage.destination_path) / "backy_backups" / "test_db"
        )

    def test_upload_success_directory(self, tmp_path):
        """
        Test that upload successfully copies a directory to the destination path.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary directory with files to upload
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")
        (test_dir / "file2.txt").write_text("File 2 content")
        # Call the upload method and check the result
        uploaded_path = local_storage.upload(str(test_dir))
        assert Path(uploaded_path).exists()
        assert (Path(uploaded_path) / "file1.txt").exists()
        assert (Path(uploaded_path) / "file2.txt").exists()
        assert (Path(uploaded_path) / "file1.txt").read_text() == "File 1 content"
        assert (Path(uploaded_path) / "file2.txt").read_text() == "File 2 content"
        assert (
            Path(uploaded_path).parent
            == Path(local_storage.destination_path) / "backy_backups" / "test_db"
        )

    def test_upload_failure_file_no_file_path(self, caplog):
        """
        Test that upload fails when no file path is provided.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Call the upload method with an empty string and check the exception
        with pytest.raises(FileNotFoundError) as exc_info:
            local_storage.upload("")
        assert "File not provided or does not exist" in caplog.text
        assert "File not provided or does not exist" in str(exc_info.value)

    def test_upload_failure_file_not_exist(self, caplog):
        """
        Test that upload fails when the provided file does not exist.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Call the upload method with a non-existent file path and check the exception
        with pytest.raises(FileNotFoundError) as exc_info:
            local_storage.upload("/non/existent/file.txt")
        assert "File not provided or does not exist" in caplog.text
        assert "File not provided or does not exist" in str(exc_info.value)

    def test_upload_failure_not_file_or_directory(self, mocker, caplog):
        """
        Test that upload fails when the provided path is neither a file nor a directory.
        """
        storage = LocalStorage(db_name="test")
        # Mock the Path methods to simulate a non-file and non-directory
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=False)
        mocker.patch("pathlib.Path.is_dir", return_value=False)
        mocker.patch(
            "pathlib.Path.name",
            new_callable=mocker.PropertyMock,
            return_value="weird_thing",
        )
        # Call the upload method with a non-file and non-directory path and check the exception
        with pytest.raises(ValueError) as exc_info:
            storage.upload("/fake/path/weird_thing")
        assert "Provided path is neither a file nor a directory." in str(exc_info.value)
        assert "Provided path is neither a file nor a directory." in caplog.text

    def test_upload_failure_runtime_error(self, tmp_path, mocker, caplog):
        """
        Test that upload raises RuntimeError on unexpected exceptions.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        mocker.patch("shutil.copy2", side_effect=Exception("Unexpected error"))
        # Call the upload method and check the exception with generic error handling
        with pytest.raises(RuntimeError) as exc_info:
            local_storage.upload(str(test_file))
        assert "Failed to upload file: Unexpected error" in str(exc_info.value)
        assert "Failed to upload file: Unexpected error" in caplog.text

    def test_download_success_file(self, tmp_path):
        """
        Test that download successfully copies a file from the destination path to the processing path.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to download
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Call the download method and check the result
        downloaded_path = local_storage.download(str(test_file))
        assert Path(downloaded_path).exists()
        assert Path(downloaded_path).read_text() == "This is a test file."
        assert Path(downloaded_path).parent == Path(local_storage.processing_path)

    def test_download_success_directory(self, tmp_path):
        """
        Test that download successfully copies a directory from the destination path to the processing path.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary directory with files to download
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")
        (test_dir / "file2.txt").write_text("File 2 content")
        # Call the download method and check the result
        downloaded_path = local_storage.download(str(test_dir))
        assert Path(downloaded_path).exists()
        assert (Path(downloaded_path) / "file1.txt").exists()
        assert (Path(downloaded_path) / "file2.txt").exists()
        assert (Path(downloaded_path) / "file1.txt").read_text() == "File 1 content"
        assert (Path(downloaded_path) / "file2.txt").read_text() == "File 2 content"
        assert Path(downloaded_path) == Path(local_storage.processing_path)

    def test_download_failure_file_no_file_path(self, caplog):
        """
        Test that download fails when no file path is provided.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Call the download method with an empty string and check the exception
        with pytest.raises(FileNotFoundError) as exc_info:
            local_storage.download("")
        assert "File not provided or does not exist" in caplog.text
        assert "File not provided or does not exist" in str(exc_info.value)

    def test_download_failure_file_not_exist(self, caplog):
        """
        Test that download fails when the file does not exist.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Call the download method with a non-existent file path and check the exception
        with pytest.raises(FileNotFoundError) as exc_info:
            local_storage.download("/non/existent/file.txt")
        assert "File not provided or does not exist" in caplog.text
        assert "File not provided or does not exist" in str(exc_info.value)

    def test_download_failure_not_file_or_directory(self, mocker, caplog):
        """
        Test that download fails when the provided path is neither a file nor a directory.
        """
        storage = LocalStorage(db_name="test")
        # Mock the Path methods to simulate a non-file and non-directory
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=False)
        mocker.patch("pathlib.Path.is_dir", return_value=False)
        mocker.patch(
            "pathlib.Path.name",
            new_callable=mocker.PropertyMock,
            return_value="weird_thing",
        )
        # Call the download method with a non-file and non-directory path and check the exception
        with pytest.raises(ValueError) as exc_info:
            storage.download("/fake/path/weird_thing")
        assert "Provided path is neither a file nor a directory." in str(exc_info.value)
        assert "Provided path is neither a file nor a directory." in caplog.text

    def test_download_failure_runtime_error(self, tmp_path, mocker, caplog):
        """
        Test that download raises RuntimeError on unexpected exceptions.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to download
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        mocker.patch("shutil.copy2", side_effect=Exception("Unexpected error"))
        # Call the download method and check the exception with generic error handling
        with pytest.raises(RuntimeError) as exc_info:
            local_storage.download(str(test_file))
        assert "Failed to download file: Unexpected error" in str(exc_info.value)
        assert "Failed to download file: Unexpected error" in caplog.text

    def test_delete_file_success(self, tmp_path):
        """
        Test that delete_file successfully removes a file from local storage.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to delete
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Call the delete method and check the result
        local_storage.delete(str(test_file))
        assert not test_file.exists()

    def test_delete_directory_success(self, tmp_path):
        """
        Test that delete_directory successfully removes a directory from local storage.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary directory with files to delete
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")
        (test_dir / "file2.txt").write_text("File 2 content")
        # Call the delete method and check the result
        local_storage.delete(str(test_dir))
        assert not test_dir.exists()
        assert not (test_dir / "file1.txt").exists()
        assert not (test_dir / "file2.txt").exists()

    def test_delete_not_file_or_directory(self, mocker, caplog):
        """
        Test that delete raises ValueError when the provided path is neither a file nor a directory.
        """
        storage = LocalStorage(db_name="test")
        # Mock the Path methods to simulate a non-file and non-directory
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch("pathlib.Path.is_file", return_value=False)
        mocker.patch("pathlib.Path.is_dir", return_value=False)
        mocker.patch(
            "pathlib.Path.name",
            new_callable=mocker.PropertyMock,
            return_value="weird_thing",
        )
        # Call the delete method with a non-file and non-directory path and check the exception
        with pytest.raises(ValueError) as exc_info:
            storage.delete("/fake/path/weird_thing")
        assert "Provided path is neither a file nor a directory." in str(exc_info.value)
        assert "Provided path is neither a file nor a directory." in caplog.text

    def test_delete_runtime_error(self, tmp_path, mocker, caplog):
        """
        Test that delete raises RuntimeError on unexpected exceptions.
        """
        local_storage = LocalStorage(db_name="test_db")
        # Create a temporary file to delete
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        mocker.patch("pathlib.Path.unlink", side_effect=Exception("Unexpected error"))
        # Call the delete method and check the exception with generic error handling
        with pytest.raises(RuntimeError) as exc_info:
            local_storage.delete(str(test_file))
        assert "Failed to delete file: Unexpected error" in str(exc_info.value)
        assert "Failed to delete file: Unexpected error" in caplog.text
