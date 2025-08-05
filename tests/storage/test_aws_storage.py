# tests/storage/test_aws_storage.py
import pytest
from storage.aws_storage import AWSStorage
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import os
from pathlib import Path
import boto3

load_dotenv()


class TestAWSStorage:
    """
    Tests for the AWSStorage class.
    """

    @pytest.fixture
    def aws_storage(self, monkeypatch, mocker):
        """
        Mocking AWS S3 client for testing.
        """
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "test-bucket")
        mocker.patch("boto3.client", return_value=mocker.Mock())
        return AWSStorage(db_name="test_db")

    def test_upload_files_success(self, aws_storage, tmp_path, mocker):
        """
        Test uploading a file to AWS S3.
        """
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Mock the S3 methods inside AWSStorage upload method
        mocker.patch.object(
            aws_storage.s3, "upload_file", return_value="/backup/test_file.txt"
        )
        mocker.patch.object(
            aws_storage, "generate_dest_path", return_value="backup/test_file.txt"
        )
        # Call the upload method and check the result
        result = aws_storage.upload(str(test_file))
        assert result == "backup/test_file.txt"
        aws_storage.s3.upload_file.assert_called_once_with(
            str(test_file), "test-bucket", aws_storage.generate_dest_path(test_file)
        )

    def test_upload_file_not_found(self, aws_storage, caplog):
        """
        Test uploading a file that does not exist.
        """
        # Calling upload with a non-existent file and checking for FileNotFoundError
        with pytest.raises(FileNotFoundError) as excinfo:
            aws_storage.upload("non_existent_file.txt")
        assert "File not provided or does not exist." in caplog.text
        assert "File not provided or does not exist" in str(excinfo.value)

    def test_upload_file_failure(self, aws_storage, tmp_path, mocker):
        """
        Test uploading a file that fails due to S3 client error.
        """
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Mock the S3 upload method to raise a ClientError
        mocker.patch.object(
            aws_storage.s3,
            "upload_file",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "Upload"
            ),
        )
        mocker.patch.object(
            aws_storage, "generate_dest_path", return_value="backup/test_file.txt"
        )
        # Call the upload method and check for RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            aws_storage.upload(str(test_file))
        assert "Failed to upload file to S3." in str(excinfo.value)

    def test_download_file_success(self, aws_storage, tmp_path, mocker):
        """
        Test downloading a file from AWS S3.
        """
        # Mock the S3 methods inside AWSStorage download method
        mocker.patch.object(aws_storage.s3, "download_file", return_value=None)
        # Call the download method and check the result
        result = aws_storage.download("backup/test_file.txt")
        expected_path = str(Path(os.getenv("MAIN_BACKUP_PATH")) / "test_file.txt")
        assert result == expected_path
        aws_storage.s3.download_file.assert_called_once_with(
            "test-bucket", "backup/test_file.txt", expected_path
        )

    def test_download_file_failure(self, aws_storage, mocker):
        """
        Test downloading a file that fails due to S3 client error.
        """
        # Mock the S3 download method to raise a ClientError
        mocker.patch.object(
            aws_storage.s3,
            "download_file",
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "Download"
            ),
        )
        # Call the download method and check for RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            aws_storage.download("backup/test_file.txt")
        assert "Failed to download file from S3." in str(excinfo.value)

    def test_validate_credentials_success(self, aws_storage, mocker):
        """
        Test validating AWS credentials.
        """
        # Mock the S3 methods inside AWSStorage validate_credentials method
        mocker.patch.object(
            aws_storage.s3,
            "list_buckets",
            return_value={"LocationConstraint": "us-west-2"},
        )
        # Call the validate_credentials method and check the result
        assert aws_storage.validate_credentials() is True
        assert aws_storage.s3.list_buckets.called

    def test_validate_credentials_no_bucket(self, aws_storage, caplog):
        """
        Test validating AWS credentials when bucket name is not set.
        """
        # Ensure bucket name is not set and check for warning
        aws_storage.bucket_name = None
        assert aws_storage.validate_credentials() is False
        assert "AWS S3 bucket name is not set." in caplog.text

    def test_validate_credentials_no_processing_path(self, aws_storage, caplog):
        """
        Test validating AWS credentials when processing path is not set.
        """
        # Ensure processing path is not set and check for warning
        aws_storage.processing_path = None
        assert aws_storage.validate_credentials() is False
        assert "Processing path is not set or does not exist." in caplog.text

    def test_validate_credentials_no_processing_path_exists(self, aws_storage, caplog):
        """
        Test validating AWS credentials when processing path does not exist.
        """
        # Ensure processing path does not exist and check for warning
        aws_storage.processing_path = "/non/existent/path"
        assert aws_storage.validate_credentials() is False
        assert "Processing path is not set or does not exist." in caplog.text

    def test_validate_credentials_no_buckets(self, aws_storage, mocker, caplog):
        """
        Test validating AWS credentials when no buckets are available.
        """
        # Mock the S3 list_buckets method to raise NoCredentialsError
        mocker.patch.object(
            aws_storage.s3, "list_buckets", side_effect=NoCredentialsError()
        )
        assert aws_storage.validate_credentials() is False
        assert "AWS credentials are not available." in caplog.text

    def test_validate_credentials_client_error(self, aws_storage, mocker, caplog):
        """
        Test validating AWS credentials when a client error occurs.
        """
        # Mock the S3 list_buckets method to raise ClientError
        mocker.patch.object(
            aws_storage.s3,
            "list_buckets",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "ListBuckets",
            ),
        )
        assert aws_storage.validate_credentials() is False
        assert "Failed to access AWS S3 bucket." in caplog.text

    def test_delete_file_success(self, aws_storage, mocker, caplog):
        """
        Test deleting a file from AWS S3.
        """
        # Mock the S3 methods inside AWSStorage delete method
        mocker.patch.object(aws_storage.s3, "delete_object", return_value=None)
        # Call the delete method and check the result
        result = aws_storage.delete("backup/test_file.txt")
        assert result is True
        aws_storage.s3.delete_object.assert_called_once_with(
            Bucket=aws_storage.bucket_name, Key="backup/test_file.txt"
        )
        assert "File deleted successfully from S3: backup/test_file.txt" in caplog.text

    def test_delete_file_failure(self, aws_storage, mocker):
        """
        Test deleting a file that fails due to S3 client error.
        """
        # Mock the S3 delete_object method to raise ClientError
        mocker.patch.object(
            aws_storage.s3,
            "delete_object",
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "DeleteObject"
            ),
        )
        # Call the delete method and check for RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            aws_storage.delete("backup/test_file.txt")
        assert "Failed to delete file from S3." in str(excinfo.value)

    @pytest.fixture
    def live_aws_storage(self, tmp_path, monkeypatch):
        """
        Fixture to create a live AWSStorage instance with real credentials.
        This requires valid AWS credentials to run.
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
        # Create a temporary file to upload
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Call the AWSStorage constructor with the bucket name
        aws_storage = AWSStorage(db_name="test_db")
        # Patch the bucket name
        yield aws_storage, test_file
        # Cleanup: delete the test file from S3 after the test
        aws_storage.s3.delete_object(
            Bucket=aws_storage.bucket_name, Key="backy_backups/test_db/test_file.txt"
        )

    @pytest.mark.usefixtures("require_localstack")
    def test_validate_credentials_real(self, live_aws_storage):
        """
        Test validating AWS credentials with a live AWSStorage instance.
        This test requires valid AWS credentials to run.
        """
        aws_storage, _ = live_aws_storage
        assert aws_storage.validate_credentials() is True

    @pytest.mark.usefixtures("require_localstack")
    def test_upload_real_file(self, live_aws_storage):
        """
        Test uploading a real file to AWS S3.
        This test requires valid AWS credentials to run.
        """
        aws_storage, test_file = live_aws_storage
        result = aws_storage.upload(str(test_file))
        assert result == f"backy_backups/{aws_storage.db_name}/{test_file.name}"

    @pytest.mark.usefixtures("require_localstack")
    def test_download_real_file(self, live_aws_storage):
        """
        Test downloading a real file from AWS S3.
        This test requires valid AWS credentials to run.
        """
        aws_storage, test_file = live_aws_storage
        # First, upload the file to S3
        aws_storage.s3.upload_file(
            str(test_file),
            aws_storage.bucket_name,
            f"backy_backups/{aws_storage.db_name}/{test_file.name}",
        )
        # Now, download the file
        result = aws_storage.download(
            f"backy_backups/{aws_storage.db_name}/{test_file.name}"
        )
        # Check the results
        assert Path(result).exists()
        assert Path(result).read_text() == "This is a test file."
        assert result == str(Path(os.getenv("MAIN_BACKUP_PATH")) / "test_file.txt")

    @pytest.mark.usefixtures("require_localstack")
    def test_delete_real_file(self, live_aws_storage):
        """
        Test deleting a real file from AWS S3.
        This test requires valid AWS credentials to run.
        """
        aws_storage, test_file = live_aws_storage
        # First, upload the file to S3
        aws_storage.s3.upload_file(
            str(test_file),
            aws_storage.bucket_name,
            f"backy_backups/{aws_storage.db_name}/{test_file.name}",
        )
        # Now, delete the file
        result = aws_storage.delete(
            f"backy_backups/{aws_storage.db_name}/{test_file.name}"
        )
        # Check the result
        assert result is True
