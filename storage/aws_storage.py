# storage/aws_storage.py
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from pathlib import Path
from storage.storage_base import StorageBase
from dotenv import load_dotenv
import os

load_dotenv()


class AWSStorage(StorageBase):
    """
    AWS S3 storage implementation for the Backy project.
    This class provides methods to upload, download, and validate credentials
    for files in AWS S3.
    """

    def __init__(self, db_name: str):
        """
        Initialize the S3 storage engine with AWS credentials.
        """
        super().__init__(db_name)
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        self.processing_path = os.getenv("MAIN_BACKUP_PATH", None)
        self.s3 = boto3.client("s3")

    def upload(self, file_path: str) -> str:
        """
        Upload a file to AWS S3.
        Args:
            file_path (str): The path to the file to be uploaded.
        Returns:
            str: The S3 path to the uploaded file.
        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If the upload fails.
        """
        # Check if the file exists and is provided
        if not file_path or not Path(file_path).exists():
            self.logger.error("File not provided or does not exist.")
            raise FileNotFoundError("File not provided or does not exist")

        try:
            # Generate the herarchical path for the file in S3
            dest_path = self.generate_dest_path(file_path)
            # Upload the file to S3
            self.s3.upload_file(file_path, self.bucket_name, dest_path)
            self.logger.info(f"File uploaded successfully to {dest_path}")
            return str(dest_path)
        except ClientError as e:
            self.logger.error(f"Failed to upload file to S3: {e}")
            raise RuntimeError("Failed to upload file to S3.") from e

    def download(self, file_path: str) -> str:
        """
        Download a file from AWS S3 to the local path.
        Args:
            file_path (str): The S3 path of the file to be downloaded.
        Returns:
            str: The local path where the file is downloaded.
        Raises:
            RuntimeError: If the download fails.
        """
        try:
            # Download the file from S3
            destination = Path(self.processing_path) / Path(file_path).name
            self.s3.download_file(self.bucket_name, file_path, str(destination))
            return str(destination)
        except ClientError as e:
            self.logger.error(f"Failed to download file from S3: {e}")
            raise RuntimeError("Failed to download file from S3.") from e

    def validate_credentials(self) -> bool:
        """
        Validate the AWS credentials for S3.
        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        # Check if the bucket name is set to environment variable
        if not self.bucket_name:
            self.logger.error("AWS S3 bucket name is not set.")
            return False
        # Check if the processing path is set and exists
        if not self.processing_path or not Path(self.processing_path).exists():
            self.logger.error("Processing path is not set or does not exist.")
            return False

        try:
            # Attempt to list the buckets to validate credentials
            self.s3.list_buckets()
            self.logger.info("AWS S3 credentials validated successfully.")
            return True
        except NoCredentialsError:
            self.logger.error("AWS credentials are not available.")
            return False
        except ClientError:
            self.logger.error("Failed to access AWS S3 bucket.")
            return False

    def delete(self, file_path: str) -> bool:
        """
        Delete a file from AWS S3.
        Args:
            file_path (str): The S3 path of the file to be deleted.
        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        Raises:
            RuntimeError: If the deletion fails.
        """
        try:
            # Delete the file from S3
            self.s3.delete_object(Bucket=self.bucket_name, Key=file_path)
            self.logger.info(f"File deleted successfully from S3: {file_path}")
            return True
        except ClientError as e:
            self.logger.error(f"Failed to delete file from S3: {e}")
            raise RuntimeError("Failed to delete file from S3.") from e
