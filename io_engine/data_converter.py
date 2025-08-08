# io_engine/data_converter.py
from logger.logger_manager import LoggerManager


class DataConverter:
    """
    This class provides methods to convert data between different formats,
    specifically between string and bytes.
    It includes error handling to ensure that the data is in the correct format
    before conversion and logs any errors that occur during the process.
    """

    def __init__(self):
        """
        Initialize the DataConverter with a logger.
        """
        self.logger = LoggerManager.setup_logger("io_engine")

    def convert_str_to_bytes(self, data: str) -> bytes:
        """
        Convert the given data to bytes.
        Args:
            data (str): The string data to convert.
        Returns:
            bytes: The converted data format.
        Raises:
            TypeError: If the data is not a string.
            RuntimeError: If the conversion fails.
        """
        if not isinstance(data, str):
            self.logger.error("Data must be a string.")
            raise TypeError("Data must be a string.")

        try:
            converted_data = data.encode("utf-8")
            return converted_data
        except Exception as e:
            self.logger.error(f"Failed to convert data to bytes: {e}")
            raise RuntimeError("Failed to convert data to bytes.") from e

    def convert_bytes_to_str(self, data: bytes) -> str:
        """
        Convert the given data to a string.
        Args:
            data (bytes): The bytes data to convert.
        Returns:
            str: The converted data format.
        Raises:
            TypeError: If the data is not bytes.
            RuntimeError: If the conversion fails.
        """
        if not isinstance(data, bytes):
            self.logger.error("Data must be bytes.")
            raise TypeError("Data must be bytes.")

        try:
            converted_data = data.decode("utf-8")
            return converted_data
        except Exception as e:
            self.logger.error(f"Failed to convert data to string: {e}")
            raise RuntimeError("Failed to convert data to string.") from e
