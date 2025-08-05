# tests/integration/test_storage_integration.py
import pytest
from storage.storage_manager import StorageManager
from dotenv import load_dotenv
from pathlib import Path
import boto3

load_dotenv()


class TestStorageIntegration:
    """
    Test suite for the StorageManager class to ensure integration with different storage backends.
    """

    @pytest.fixture
    def local_storage_manager(self, monkeypatch, tmp_path):
        """
        Fixture to create a StorageManager instance for local storage.
        """
        # Set the local path for local storage
        local_path = tmp_path / "backy_local_storage"
        local_path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("LOCAL_PATH", str(local_path))
        # Initialize the StorageManager with the specified storage type
        config = {"storage_type": "local", "db_name": "test_backy_db"}
        return StorageManager(config)

    def test_validate_credentials_success_local_storage(self, local_storage_manager):
        """
        Test the validate_credentials method of the StorageManager.
        """
        assert local_storage_manager.storage.validate_credentials() is True

    def test_upload_success_local_storage(self, local_storage_manager, tmp_path):
        """
        Test the upload functionality of the StorageManager.
        """
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file using the StorageManager
        uploaded_path = local_storage_manager.upload(str(test_file))
        # Check if the uploaded path is not None and matches the expected format
        assert uploaded_path is not None
        assert Path(uploaded_path).name == test_file.name
        # Clean up by deleting the uploaded file
        local_storage_manager.delete(uploaded_path)

    def test_upload_invalid_file_local_storage(self, local_storage_manager):
        """
        Test the upload functionality with an invalid file path.
        """
        with pytest.raises(FileNotFoundError):
            local_storage_manager.upload("non_existent_file.txt")

    def test_download_success_local_storage(self, local_storage_manager, tmp_path):
        """
        Test the download functionality of the StorageManager.
        """
        # Create a temporary file to upload and then download
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then download it
        uploaded_path = local_storage_manager.upload(str(test_file))
        downloaded_path = local_storage_manager.download(uploaded_path)
        # Check if the downloaded path is not None and the content matches
        assert downloaded_path is not None
        assert Path(downloaded_path).read_text() == "This is a test file."
        # Clean up by deleting the uploaded file
        local_storage_manager.delete(uploaded_path)

    def test_download_invalid_file_local_storage(self, local_storage_manager):
        """
        Test the download functionality with an invalid file path.
        """
        with pytest.raises((FileNotFoundError, RuntimeError)):
            local_storage_manager.download("non_existent_file.txt")

    def test_delete_success_local_storage(self, local_storage_manager, tmp_path):
        """
        Test the delete functionality of the StorageManager.
        """
        # Create a temporary file to upload and then delete
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then delete it
        uploaded_path = local_storage_manager.upload(str(test_file))
        # Delete the uploaded file
        local_storage_manager.delete(uploaded_path)
        # Check if the file is deleted by trying to download it
        with pytest.raises((FileNotFoundError, RuntimeError)):
            local_storage_manager.download(uploaded_path)

    def test_delete_not_found_local_storage(self, local_storage_manager, tmp_path):
        """
        Test the delete functionality with a non-existent file path.
        It silently skips the test if the file does not exist.
        """
        # Create a temporary file to delete
        test_file = tmp_path / "non_existent_file.txt"
        test_file.touch()
        # Attempt to delete not found file
        local_storage_manager.delete(str(test_file))

    @pytest.fixture
    def s3_storage_manager(self, monkeypatch):
        """
        Fixture to create a StorageManager instance for S3 storage.
        This fixture requires LocalStack to be running.
        """
        # Set environment variables for AWS credentials
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "backy-backups")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        # Create a mock S3 client
        s3_client = boto3.client("s3", endpoint_url="http://localhost:4566")
        # Create a bucket for testing
        s3_client.create_bucket(Bucket="backy-backups")
        # Patch the boto3 client to use the mock S3 client
        monkeypatch.setattr("boto3.client", lambda *args, **kwargs: s3_client)
        # Initialize the StorageManager with the specified storage type
        config = {"storage_type": "aws", "db_name": "test_backy_db"}
        return StorageManager(config)

    @pytest.mark.usefixtures("require_localstack")
    def test_validate_credentials_success_aws_storage(self, s3_storage_manager):
        """
        Test the validate_credentials method of the StorageManager.
        """
        assert s3_storage_manager.storage.validate_credentials() is True

    @pytest.mark.usefixtures("require_localstack")
    def test_upload_success_aws_storage(self, s3_storage_manager, tmp_path):
        """
        Test the upload functionality of the StorageManager.
        """
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file using the StorageManager
        uploaded_path = s3_storage_manager.upload(str(test_file))
        # Check if the uploaded path is not None and matches the expected format
        assert uploaded_path is not None
        assert Path(uploaded_path).name == test_file.name
        # Clean up by deleting the uploaded file
        s3_storage_manager.delete(uploaded_path)

    @pytest.mark.usefixtures("require_localstack")
    def test_upload_invalid_file_aws_storage(self, s3_storage_manager):
        """
        Test the upload functionality with an invalid file path.
        """
        with pytest.raises(FileNotFoundError):
            s3_storage_manager.upload("non_existent_file.txt")

    @pytest.mark.usefixtures("require_localstack")
    def test_download_success_aws_storage(self, s3_storage_manager, tmp_path):
        """
        Test the download functionality of the StorageManager.
        """
        # Create a temporary file to upload and then download
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then download it
        uploaded_path = s3_storage_manager.upload(str(test_file))
        downloaded_path = s3_storage_manager.download(uploaded_path)
        # Check if the downloaded path is not None and the content matches
        assert downloaded_path is not None
        assert Path(downloaded_path).read_text() == "This is a test file."
        # Clean up by deleting the uploaded file
        s3_storage_manager.delete(uploaded_path)

    @pytest.mark.usefixtures("require_localstack")
    def test_download_invalid_file_aws_storage(self, s3_storage_manager):
        """
        Test the download functionality with an invalid file path.
        """
        with pytest.raises((FileNotFoundError, RuntimeError)):
            s3_storage_manager.download("non_existent_file.txt")

    @pytest.mark.usefixtures("require_localstack")
    def test_delete_success_aws_storage(self, s3_storage_manager, tmp_path):
        """
        Test the delete functionality of the StorageManager.
        """
        # Create a temporary file to upload and then delete
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Upload the file and then delete it
        uploaded_path = s3_storage_manager.upload(str(test_file))
        # Delete the uploaded file
        s3_storage_manager.delete(uploaded_path)
        # Check if the file is deleted by trying to download it
        with pytest.raises((FileNotFoundError, RuntimeError)):
            s3_storage_manager.download(uploaded_path)

    @pytest.mark.usefixtures("require_localstack")
    def test_delete_not_found_aws_storage(self, s3_storage_manager, tmp_path):
        """
        Test the delete functionality with a non-existent file path.
        It silently skips the test if the file does not exist.
        """
        # Create a temporary file to delete
        test_file = tmp_path / "non_existent_file.txt"
        test_file.touch()
        # Attempt to delete not found file
        s3_storage_manager.delete(str(test_file))
