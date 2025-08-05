# storage/local_storage.py
import shutil
from pathlib import Path
from storage.storage_base import StorageBase
from dotenv import load_dotenv
import os

load_dotenv()


class LocalStorage(StorageBase):
    """
    Local storage implementation for the Backy project.
    This class provides methods to upload, download, and delete files
    in the local file system.
    """

    def __init__(self, db_name: str):
        """
        Initialize the local storage engine.
        """
        super().__init__(db_name)
        self.destination_path = os.getenv("LOCAL_PATH", None)
        self.processing_path = os.getenv("MAIN_BACKUP_PATH", None)

    def upload(self, file_path: str) -> str:
        """
        Move the file that contains the backups files and maybe to another location
        Args:
            file_path (str): The path to the file to be uploaded.
        Returns:
            str: The path to the uploaded file in local storage.
        Raises:
            FileNotFoundError: If the provided file does not exist.
            ValueError: If the provided path is neither a file nor a directory.
            RuntimeError: If the upload fails.
        """
        try:
            # Check if the file exists and is provided
            if not file_path or not Path(file_path).exists():
                self.logger.error("File not provided or does not exist.")
                raise FileNotFoundError("File not provided or does not exist")

            # Generate the hierarchical path for the file in local storage and ensure the directory exists
            dest_rel_path = self.generate_dest_path(file_path)
            destination = Path(self.destination_path) / dest_rel_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            file_path = Path(file_path)

            # Copy the file or directory to the destination
            if file_path.is_file():
                shutil.copy2(file_path, destination)
            elif file_path.is_dir():
                shutil.copytree(file_path, destination, dirs_exist_ok=True)
            else:
                self.logger.error("Provided path is neither a file nor a directory.")
                raise ValueError("Provided path is neither a file nor a directory.")

            return str(destination)
        except Exception as e:
            if isinstance(e, FileNotFoundError) or isinstance(e, ValueError):
                raise e
            self.logger.error(f"Failed to upload file: {e}")
            raise RuntimeError(f"Failed to upload file: {e}")

    def download(self, file_path: str) -> str:
        """
        Download a file from local storage to the specified destination.
        Args:
            file_path (str): The path to the file to be downloaded.
        Returns:
            str: The path to the downloaded file in local storage.
        Raises:
            FileNotFoundError: If the provided file does not exist.
            ValueError: If the provided path is neither a file nor a directory.
            RuntimeError: If the download fails.
        """
        try:
            # Check if the file exists and is provided
            if not file_path or not Path(file_path).exists():
                self.logger.error("File not provided or does not exist.")
                raise FileNotFoundError("File not provided or does not exist")

            # Convert file path and processing path to Path objects
            file_path = Path(file_path)
            process_path = Path(self.processing_path)

            # Copy the file or directory to the processing path then delete the original
            if file_path.is_file():
                destination = process_path / file_path.name
                shutil.copy2(file_path, destination)
                return str(destination)
            elif file_path.is_dir():
                shutil.copytree(file_path, process_path, dirs_exist_ok=True)
                return str(process_path)
            else:
                self.logger.error("Provided path is neither a file nor a directory.")
                raise ValueError("Provided path is neither a file nor a directory.")

        except Exception as e:
            if isinstance(e, FileNotFoundError) or isinstance(e, ValueError):
                raise e
            self.logger.error(f"Failed to download file: {e}")
            raise RuntimeError(f"Failed to download file: {e}")

    def validate_credentials(self) -> bool:
        """
        Validate the credentials for local storage.
        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        # Check if the destination path is set and exists
        if not self.destination_path or not Path(self.destination_path).exists():
            self.logger.error("Local storage paths are not set or do not exist.")
            return False

        # Check if the processing path is set and exists
        if not self.processing_path or not Path(self.processing_path).exists():
            self.logger.error("Processing path is not set or does not exist.")
            return False

        self.logger.info("Local storage credentials validated successfully.")
        return True

    def delete(self, file_path: str) -> None:
        """
        Delete a file from local storage.
        Args:
            file_path (str): The path to the file to be deleted.
        Raises:
            ValueError: If the provided path is neither a file nor a directory.
            RuntimeError: If the delete operation fails.
        """
        try:
            # Convert file path to Path object
            file_path = Path(file_path)

            # Delete the file or directory
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                self.logger.error("Provided path is neither a file nor a directory.")
                raise ValueError("Provided path is neither a file nor a directory.")

            self.logger.info(f"File deleted successfully: {file_path}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            self.logger.error(f"Failed to delete file: {e}")
            raise RuntimeError(f"Failed to delete file: {e}")
