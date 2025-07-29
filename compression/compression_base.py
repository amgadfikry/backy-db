# compression/compression_base.py
from pathlib import Path
from dotenv import load_dotenv
import os
from abc import ABC, abstractmethod
from logger.logger_manager import LoggerManager

load_dotenv()


class CompressionBase(ABC):
    """
    A class to manage compression and decompression of files.
    This class provides methods to compress a folder into a zip file and decompress a zip file.
    """
    # Supported compression types and their associated extensions
    SUPPORTED_TYPES = {
        'zip': 'zip',
        'tar': 'tar',
        'targz': 'tar.gz'
    }

    def __init__(self, compression_type: str = 'zip'):
        """
        Initialize the CompressionManager with a specified compression type.
        Args:
            compression_type (str): Type of compression to use ('zip' or 'tar').
        """
        self.logger = LoggerManager.setup_logger("compression")
        self.compression_type = compression_type.lower()
        self.extension = self.SUPPORTED_TYPES[self.compression_type]
        self.processing_path = Path(os.getenv("MAIN_BACKUP_PATH"))

    @abstractmethod
    def compress_folder(self) -> Path:
        """
        Compress the given folder into a .zip archive preserving the folder structure.
        Then remove the original folder.
        Returns:
            Path: Path to the created archive file.
        """
        self.logger.error(f"compress_folder method not implemented in subclass {self.__class__.__name__}")
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def decompress_folder(self) -> Path:
        """
        Decompress a .zip file to a folder preserving the original structure.
        it will extract to the same directory as the zip file
        Then remove the original zip file.
        Returns:
            Path: Path to the extracted folder.
        """
        self.logger.error(f"decompress_folder method not implemented in subclass {self.__class__.__name__}")
        raise NotImplementedError("Subclasses must implement this method.")

    def get_folder_from_processing_path(self) -> Path:
        """
        Get the folder from the processing path.
        Returns:
            Path: Path to the folder to compress.
        """
        folder_path = list(self.processing_path.glob('*'))
        if not folder_path:
            self.logger.error("No folder found in the processing path to compress.")
            raise ValueError("No folder found in the processing path.")
        return folder_path[0]

    def get_compressed_file_from_processing_path(self) -> Path:
        """
        Get the compressed file from the processing path.
        Returns:
            Path: Path to the compressed file.
        """
        compressed_file = list(self.processing_path.glob(f"*.{self.extension}"))
        if not compressed_file:
            self.logger.error(f"No compressed file found in the processing path for type {self.extension}.")
            raise ValueError("No compressed file found in the processing path.")
        return compressed_file[0]
