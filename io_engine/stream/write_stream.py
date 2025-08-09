# io_engine/stream/write_stream.py
from io_engine.stream.stream_base import StreamBase
import json
import os


class WriteStream(StreamBase):
    """
    Class for writing data to a stream.
    Inherits from StreamBase and provides methods to write data to a file.
    """

    def __init__(self, file_path):
        """
        Initialize the WriteStream with the given file path.
        Args:
            file_path (str): The path to the file where data will be written.
        """
        super().__init__(file_path)
        self.threshold = 2 * 1024 * 1024  # 2 MB threshold for writing data
        self.current_size = 0

    def write_stream(self, feature_name: str, data: bytes) -> None:
        """
        Write data to the stream.
        Args:
            data (bytes): The data to be written to the stream.
            feature_name (str): The name of the feature using the stream.
        """
        try:
            # Prepare metadata for the data being written
            metadata = {
                "feature_name": feature_name,
                "size": len(data),
            }

            # Convert metadata to JSON and write it to the stream
            metadata_bytes = json.dumps(metadata).encode("utf-8")

            # Make sure to write the size of the metadata first
            metadata_length = len(metadata_bytes).to_bytes(4, "big")

            # Write metadata length, metadata, and data to the stream
            chunk = metadata_length + metadata_bytes + data
            self.stream.write(chunk)
            self.current_size += len(chunk)

            # Check if the current size exceeds the threshold
            if self.current_size >= self.threshold:
                self.logger.info(
                    f"Syncing to disk (written {self.current_size} bytes since last sync)."
                )
                os.fsync(self.stream.fileno())
                self.current_size = 0

        except Exception as e:
            self.logger.error(f"Error writing data to stream {self.file_path}: {e}")
            raise RuntimeError(f"Could not write data to stream {self.file_path}.")
