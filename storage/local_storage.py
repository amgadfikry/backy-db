# storage/local_storage.py
import shutil
from pathlib import Path
from storage.storage_base import StorageBase


class LocalStorage(StorageBase):
    """
    Local storage implementation for the Backy project.
    This class provides methods to upload, download, and delete files
    in the local file system.
    """

    def upload(self) -> Path:
        """
        Move the folder of the processing contains the backups files and maybe the
        encryption files to another location in local storage.
        Return:
            Path: The path to the new location of the folder
        """
        try:
            upload_path = Path(self.path)
            shutil.copytree(self.processed_path.parent, upload_path, dirs_exist_ok=True)
            self.logger.info(f"File uploaded successfully to {upload_path}")
            return upload_path / self.processed_path.name
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            raise RuntimeError(f"Failed to upload file: {e}")

    def download(self) -> Path:
        """
        Move the folder that contains the backups files and maybe the
        encryption files from current location to the processing folder
        where the files will be processed either decrypted and restored.
        """
        try:
            current_path = Path(self.path)
            shutil.copytree(current_path, self.processed_path, dirs_exist_ok=True)
            self.logger.info(f"File downloaded successfully to {self.processed_path}")
            return self.processed_path
        except Exception as e:
            self.logger.error(f"Failed to download file: {e}")
            raise RuntimeError(f"Failed to download file: {e}")
