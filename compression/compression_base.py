# compression/compression_base.py
from pathlib import Path
from dotenv import load_dotenv
import os
from abc import ABC, abstractmethod
from logger.logger_manager import LoggerManager

load_dotenv()


class CompressionBase(ABC):
    """
    A base class for compression operations.
    This class defines the interface for compression and decompression methods.
    It should be inherited by specific compression implementations like ZipCompression.
    """

    # Supported compression types and their associated extensions
    SUPPORTED_TYPES = {"zip": ".zip", "tar": ".tar"}

    def __init__(self, compression_type: str = "zip"):
        """
        Initialize the CompressionManager with a specified compression type.
        Args:
            compression_type (str): Type of compression to use eg. 'zip' or 'tar'.
        Raises:
            ValueError: If the compression type is not supported.
        """
        self.logger = LoggerManager.setup_logger("compression")
        self.compression_type = compression_type.lower()
        if self.compression_type not in self.SUPPORTED_TYPES:
            self.logger.error(f"Unsupported compression type: {self.compression_type}")
            raise ValueError(f"Unsupported compression type: {self.compression_type}")
        self.extension = self.SUPPORTED_TYPES[self.compression_type]
        self.processing_path = Path(os.getenv("MAIN_BACKUP_PATH"))

    @abstractmethod
    def compress_folder(self, folder_path: Path) -> Path:
        """
        Compress the given folder into a .zip archive preserving the folder structure.
        Then remove the original folder.
        Args:
            folder_path (Path): Path to the folder to compress.
        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        Returns:
            Path: Path to the created archive file.
        """
        self.logger.error(
            f"compress_folder method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def decompress_folder(self, folder_path: Path) -> Path:
        """
        Decompress the given .zip archive into a folder.
        Args:
            file_path (Path): Path to the compressed file.
        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        Returns:
            Path: Path to the extracted folder.
        """
        self.logger.error(
            f"decompress_folder method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def compress_bytes(self, data: bytes) -> bytes:
        """
        Compress the given bytes.
        Args:
            data (bytes): Data to compress.
        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        Returns:
            bytes: Compressed data.
        """
        self.logger.error(
            f"compress_bytes method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def decompress_bytes(self, data: bytes) -> bytes:
        """
        Decompress the given bytes.
        Args:
            data (bytes): Data to decompress.
        Raises:
            NotImplementedError: If the method is not implemented in the subclass.
        Returns:
            bytes: Decompressed data.
        """
        self.logger.error(
            f"decompress_bytes method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")
