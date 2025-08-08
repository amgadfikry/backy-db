# io_engine/stream/stream_base.py
from logger.logger_manager import LoggerManager
from pathlib import Path
from typing import BinaryIO


class StreamBase:
    """
    Abstract base class for all stream types.
    This class provides a common interface for writing data to streams.
    """

    def __init__(self, file_path: Path):
        """
        Initialize the StreamBase with a specific file path.
        Args:
            file_path (Path): The path to the file where data will be written.
        """
        self.file_path = file_path
        self.logger = LoggerManager.setup_logger("io_engine")
        self.stream: BinaryIO | None = None
        self.mode = self._identify_mode()

    def _identify_mode(self) -> str:
        """
        Identify the mode of the stream based on name of the child class.
        This method checks the class name to determine if the stream is for writing or reading.
        Returns:
            str: The mode of the stream ('w' for write, 'r' for read).
        """
        if self.__class__.__name__ == "WriteStream":
            return "wb"
        elif self.__class__.__name__ == "ReadStream":
            return "rb"
        else:
            self.logger.error(f"Unknown stream type: {self.__class__.__name__}.")
            raise ValueError(
                "Unknown stream type. Must be 'WriteStream' or 'ReadStream'."
            )

    def open_stream(self) -> object:
        """
        Open the stream for writing.
        It open the file in write mode and returns the stream object.
        Returns:
            file object: The opened stream object.
        """
        try:
            self.stream = open(self.file_path, self.mode)
            self.logger.info(f"Stream opened: {self.file_path}")
            return self.stream
        except Exception as e:
            self.logger.error(f"Error opening stream {self.file_path}: {e}")
            raise RuntimeError(f"Could not open stream {self.file_path}.")

    def close_stream(self):
        """
        Close the stream.
        This method ensures that the stream is properly closed after writing.
        """
        try:
            self.stream.close()
            self.logger.info(f"Stream closed: {self.file_path}")
        except Exception as e:
            self.logger.error(f"Error closing stream {self.file_path}: {e}")
            raise RuntimeError(f"Could not close stream {self.file_path}.")

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        This method is called when the object is used in a 'with' statement.
        Returns:
            StreamBase: The current instance of the stream.
        """
        self.open_stream()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context related to this object.
        This method is called when the 'with' statement is exited.
        Args:
            exc_type: The exception type, if any.
            exc_value: The exception value, if any.
            traceback: The traceback object, if any.
        """
        self.close_stream()
