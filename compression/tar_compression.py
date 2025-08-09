# compression/tar_compression.py
import tarfile
from pathlib import Path
import io
from compression.compression_base import CompressionBase
from utils.delete_folder import delete_folder


class TarCompression(CompressionBase):
    """
    A class to handle tar compression and decompression.
    Inherits from CompressionBase and implements methods for tar-specific operations.
    """

    def compress_folder(self, folder_path: Path) -> Path:
        """
        Compress the given folder into a .tar archive preserving the folder structure.
        Then remove the original folder.
        Args:
            folder_path (Path): Path to the folder to compress.
        Raises:
            ValueError: If the folder_path is None or does not exist or is not a directory.
            RuntimeError: If the tar file creation fails.
        Returns:
            Path: Path to the created tar file.
        """
        # Check if folder_path is None or does not exist or is not a directory, raise an error
        if folder_path is None or not folder_path.exists() or not folder_path.is_dir():
            self.logger.error(
                "No valid folder path or directory provided for compression."
            )
            raise ValueError(
                "No valid folder path or directory provided for compression."
            )

        try:
            # Determine the tar file name based on the folder name and extension
            compressed_folder_name = folder_path.parent / (
                folder_path.stem + self.extension
            )
            # Compress the folder into a tar file
            with tarfile.open(compressed_folder_name, "w") as tarf:
                for file in folder_path.rglob("*"):
                    tarf.add(file, arcname=file.relative_to(folder_path))
            # Log the successful creation of the tar file and delete the original folder
            self.logger.info(f"Successfully created tar file: {compressed_folder_name}")
            delete_folder(folder_path)
            return compressed_folder_name

        except Exception as e:
            self.logger.error(f"Failed to compress tar file: {e}")
            raise RuntimeError("Failed to compress tar file") from e

    def decompress_folder(self, folder_path: Path) -> Path:
        """
        Decompress a .tar file to a folder preserving the original structure.
        it will extract to the same directory as the tar file
        Then remove the original tar file.
        Args:
            folder_path (Path): Path to the compressed file.
        Raises:
            ValueError: If the folder_path is None or does not exist or is not a file.
            RuntimeError: If the extraction fails.
        Returns:
            Path: Path to the extracted folder.
        """
        # Check if folder_path is None or does not exist or is not a file, raise an error
        if folder_path is None or not folder_path.exists() or not folder_path.is_file():
            self.logger.error("No valid tar file path provided for decompression.")
            raise ValueError("No valid tar file path provided for decompression.")

        try:
            extracted_folder = folder_path.parent
            # Open the tar file and extract its contents
            with tarfile.open(folder_path, "r") as tarf:
                tarf.extractall(path=extracted_folder)
            # Log the successful extraction and delete the original tar file
            self.logger.info(
                f"Successfully extracted tar file: {Path(extracted_folder)}"
            )
            folder_path.unlink()
            return extracted_folder / folder_path.stem

        except Exception as e:
            self.logger.error(f"Failed to extract tar file: {e}")
            raise RuntimeError("Failed to extract tar file") from e

    def compress_bytes(self, data: bytes) -> bytes:
        """
        Compress the given bytes using tar compression.
        Args:
            data (bytes): Data to compress.
        Raises:
            ValueError: If the data is None or empty.
            RuntimeError: If the compression fails.
        Returns:
            bytes: Compressed data.
        """
        # Check if data is None or empty, raise an error
        if not data:
            self.logger.error("No data provided for compression.")
            raise ValueError("No data provided for compression.")

        try:
            # Create a virtual file object in memory to hold the tar data
            with io.BytesIO() as buf:
                # Create a tar file in write mode and add the data
                with tarfile.open(fileobj=buf, mode="w") as tarf:
                    tar_info = tarfile.TarInfo(name="data")
                    tar_info.size = len(data)
                    tarf.addfile(tar_info, fileobj=io.BytesIO(data))
                # Get the compressed data from the buffer
                self.logger.info("Successfully compressed bytes into tar format.")
                return buf.getvalue()

        except Exception as e:
            self.logger.error(f"Failed to compress bytes with tar: {e}")
            raise RuntimeError("Failed to compress bytes with tar") from e

    def decompress_bytes(self, data: bytes) -> bytes:
        """
        Decompress the given bytes using tar decompression.
        Args:
            data (bytes): Data to decompress.
        Raises:
            ValueError: If the data is None or empty.
            RuntimeError: If the decompression fails.
        Returns:
            bytes: Decompressed data.
        """
        # Check if data is None or empty, raise an error
        if not data:
            self.logger.error("No data provided for decompression.")
            raise ValueError("No data provided for decompression.")

        try:
            buf = io.BytesIO(data)

            # Open the vitual file object in memory
            with tarfile.open(fileobj=buf, mode="r") as tarf:
                members = tarf.getmembers()
                if not members:
                    self.logger.error("No files found in tar archive.")
                    raise ValueError("No files found in tar archive.")
                fileobj = tarf.extractfile(members[0])
                if fileobj is None:
                    self.logger.error("Failed to extract file from tar archive.")
                    raise ValueError("Failed to extract file from tar archive.")
                decompressed_data = fileobj.read()

            self.logger.info("Successfully decompressed bytes from tar format.")
            return decompressed_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            self.logger.error(f"Failed to decompress bytes with tar: {e}")
            raise RuntimeError("Failed to decompress bytes with tar") from e
