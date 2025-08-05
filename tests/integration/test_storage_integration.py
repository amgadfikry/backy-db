# tests/integration/test_storage_integration.py
import pytest
from storage.storage_manager import StorageManager
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def has_aws_credentials():
    """
    Check if AWS credentials are set in the environment variables.
    Returns:
        bool: True if both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set, False otherwise.
    """
    return bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))


# Parameterize the test class to run tests with different storage types
@pytest.mark.parametrize(
    "storage_type",
    [
        pytest.param("local", id="local"),
        (
            pytest.param(
                "aws",
                marks=pytest.mark.skip(
                    reason="Missing AWS credentials"
                ),  # Skip if AWS credentials are not set
                id="aws",
            )
            if not has_aws_credentials()
            else pytest.param("aws", id="aws")
        ),
    ],
)
class TestStorageIntegration:
    """
    Test suite for the StorageManager class to ensure integration with different storage backends.
    """

    @pytest.fixture
    def storage_manager(self, storage_type, monkeypatch, tmp_path):
        """
        Fixture to create a StorageManager instance based on the storage type.
        """
        # Set the local path for local storage
        local_path = tmp_path / "backy_local_storage"
        local_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("LOCAL_PATH", str(local_path))
        # Initialize the StorageManager with the specified storage type
        config = {"storage_type": storage_type, "db_name": "test_backy_db"}
        return StorageManager(config)

    def test_validate_credentials_success(self, storage_manager):
        """
        Test the validate_credentials method of the StorageManager.
        """
        assert storage_manager.storage.validate_credentials() is True

    def test_upload(self, storage_manager, tmp_path):
        """
        Test the upload functionality of the StorageManager.
        """
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file using the StorageManager
        uploaded_path = storage_manager.upload(str(test_file))
        # Check if the uploaded path is not None and matches the expected format
        assert uploaded_path is not None
        assert Path(uploaded_path).name == test_file.name
        # Clean up by deleting the uploaded file
        storage_manager.delete(uploaded_path)

    def test_upload_invalid_file(self, storage_manager):
        """
        Test the upload functionality with an invalid file path.
        """
        with pytest.raises(FileNotFoundError):
            storage_manager.upload("non_existent_file.txt")

    def test_download(self, storage_manager, tmp_path):
        """
        Test the download functionality of the StorageManager.
        """
        # Create a temporary file to upload and then download
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then download it
        uploaded_path = storage_manager.upload(str(test_file))
        downloaded_path = storage_manager.download(uploaded_path)
        # Check if the downloaded path is not None and the content matches
        assert downloaded_path is not None
        assert Path(downloaded_path).read_text() == "This is a test file."
        # Clean up by deleting the uploaded file
        storage_manager.delete(uploaded_path)

    def test_download_invalid_file(self, storage_manager):
        """
        Test the download functionality with an invalid file path.
        """
        with pytest.raises((FileNotFoundError, RuntimeError)):
            storage_manager.download("non_existent_file.txt")

    def test_delete(self, storage_manager, tmp_path):
        """
        Test the delete functionality of the StorageManager.
        """
        # Create a temporary file to upload and then delete
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then delete it
        uploaded_path = storage_manager.upload(str(test_file))
        # Delete the uploaded file
        storage_manager.delete(uploaded_path)
        # Check if the file is deleted by trying to download it
        with pytest.raises((FileNotFoundError, RuntimeError)):
            storage_manager.download(uploaded_path)

    def test_delete_not_found(self, storage_manager, tmp_path):
        """
        Test the delete functionality with a non-existent file path.
        It silently skips the test if the file does not exist.
        """
        # Create a temporary file to delete
        test_file = tmp_path / "non_existent_file.txt"
        test_file.touch()
        # Attempt to delete not found file
        storage_manager.delete(str(test_file))
