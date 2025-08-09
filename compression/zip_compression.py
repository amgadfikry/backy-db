# compression/zip_compression.py
import zipfile
import zlib
from pathlib import Path
from compression.compression_base import CompressionBase
from utils.delete_folder import delete_folder


class ZipCompression(CompressionBase):
    """
    A class to handle zip compression and decompression.
    Inherits from CompressionBase and implements methods for zip-specific operations.
    """

    def compress_folder(self, folder_path: Path) -> Path:
        """
        Compress the given folder into a .zip archive preserving the folder structure.
        Then remove the original folder.
        Args:
            folder_path (Path): Path to the folder to compress.
        Raises:
            ValueError: If the folder_path is None.
            RuntimeError: If the zip file creation fails.
        Returns:
            Path: Path to the created archive file.
        """
        # Check if folder_path is None or does not exist or is not a directory, raise an error
        if folder_path is None or not folder_path.exists() or not folder_path.is_dir():
            self.logger.error(
                "No valid folder path or directory provided for compression."
            )
            raise ValueError(
                "Not a valid folder path or directory provided for compression."
            )

        try:
            # Create a zip file with the same name as the folder and the specified extension
            compressed_folder = folder_path.parent / (folder_path.stem + self.extension)
            # Create the zip file and add the folder contents
            with zipfile.ZipFile(compressed_folder, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in folder_path.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(folder_path)
                        zipf.write(file, arcname=arcname)

            # Remove the original folder after compression
            delete_folder(folder_path)
            self.logger.info(f"Successfully created zip file: {compressed_folder}")
            return compressed_folder

        except Exception as e:
            self.logger.error(f"Failed to compress folder: {e}")
            raise RuntimeError(f"Failed to compress folder: {e}") from e

    def decompress_folder(self, folder_path: Path) -> Path:
        """
        Decompress a .zip file to a folder preserving the original structure.
        it will extract to the same directory as the zip file
        Then remove the original zip file.
        Args:
            folder_path (Path): Path to the compressed file.
        Raises:
            ValueError: If the folder_path is None or does not exist.
            RuntimeError: If the extraction fails.
        Returns:
            Path: Path to the extracted folder.
        """
        # Check if folder_path is None or does not exist, or not a compressed file, raise an error
        if (
            folder_path is None
            or not folder_path.exists()
            or not folder_path.is_file()
            or folder_path.suffix != self.extension
        ):
            self.logger.error(
                "No valid zip file path or directory provided for decompression."
            )
            raise ValueError(
                "Not a valid zip file path or directory provided for decompression."
            )

        try:
            extracted_folder = folder_path.parent
            # Open the zip file and extract its contents
            with zipfile.ZipFile(folder_path, "r") as zipf:
                if zipf.testzip() is None:
                    zipf.extractall(path=extracted_folder)
                else:
                    self.logger.error(f"Corrupted zip file: {folder_path}")
                    raise ValueError(f"Corrupted zip file: {folder_path}")
            # Log success and remove the original zip file
            self.logger.info(f"Successfully extracted zip file: {folder_path}")
            folder_path.unlink()
            return extracted_folder / folder_path.stem

        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            self.logger.error(f"Failed to extract zip file: {e}")
            raise RuntimeError(f"Failed to extract zip file: {e}") from e

    def compress_bytes(self, data: bytes) -> bytes:
        """
        Compress the given bytes using zlib compression.
        Args:
            data (bytes): Data to compress.
        Raises:
            ValueError: If the data is None or empty.
            RuntimeError: If the compression fails.
        Returns:
            bytes: Compressed data.
        """
        if not data:
            self.logger.error("No data provided for compression.")
            raise ValueError("No data provided for compression.")

        try:
            compressed_data = zlib.compress(data)
            self.logger.info("Successfully compressed bytes.")
            return compressed_data

        except Exception as e:
            self.logger.error(f"Failed to compress bytes with zlib: {e}")
            raise RuntimeError(f"Failed to compress bytes with zlib: {e}") from e

    def decompress_bytes(self, data: bytes) -> bytes:
        """
        Decompress the given bytes using zlib decompression.
        Args:
            data (bytes): Data to decompress.
        Raises:
            ValueError: If the data is None or empty.
            RuntimeError: If the decompression fails.
        Returns:
            bytes: Decompressed data.
        """
        if not data:
            self.logger.error("No data provided for decompression.")
            raise ValueError("No data provided for decompression.")
        try:
            decompressed_data = zlib.decompress(data)
            self.logger.info("Successfully decompressed bytes.")
            return decompressed_data

        except Exception as e:
            self.logger.error(f"Failed to decompress bytes with zlib: {e}")
            raise RuntimeError(f"Failed to decompress bytes with zlib: {e}") from e
