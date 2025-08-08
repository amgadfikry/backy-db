# io_engine/stream/read_stream.py
from io_engine.stream.stream_base import StreamBase
import json
from typing import Iterator, Tuple


class ReadStream(StreamBase):
    """
    Class for reading data from a stream.
    Inherits from StreamBase and provides methods to read data from a file.
    """

    def read_stream(self) -> Iterator[Tuple[str, bytes]]:
        """
        Read data from the stream.
        Returns:
            Iterator[Tuple[str, bytes]]: An iterator over feature metadata and data.
        """
        try:
            while True:
                # Read the first 4 bytes to get the size of the metadata
                metadata_size_bytes = self.stream.read(4)

                # If no data is read, it means the end of the stream has been reached
                if not metadata_size_bytes:
                    self.logger.info(
                        f"No more data to read from stream {self.file_path}."
                    )
                    return

                # If the metadata size is less than 4 bytes, raise an error
                if len(metadata_size_bytes) < 4:
                    self.logger.error("Metadata size is less than 4 bytes in stream.")
                    raise RuntimeError("Corrupted or incomplete metadata.")

                # Convert the bytes to an integer to get the size of the metadata
                metadata_size = int.from_bytes(metadata_size_bytes, "big")

                # Read the metadata based on the size
                metadata_json = self.stream.read(metadata_size)

                if len(metadata_json) < metadata_size:
                    self.logger.error("Incomplete metadata read.")
                    raise RuntimeError("Corrupted or incomplete metadata.")

                # Parse the metadata JSON
                metadata = json.loads(metadata_json.decode("utf-8"))

                # Read the data chunk based on the size specified in metadata
                data = self.stream.read(metadata["size"])

                # If the data is not read completely, raise an error
                if len(data) < metadata["size"]:
                    self.logger.error("Incomplete data chunk read.")
                    raise RuntimeError("Corrupted or incomplete data chunk.")

                # Yield the feature name and data
                yield metadata["feature_name"], data

        except Exception as e:
            self.logger.error(f"Error reading data from stream {self.file_path}: {e}")
            raise e
