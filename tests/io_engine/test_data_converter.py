# tests/io_engine/test_data_converter.py
import pytest
from io_engine.data_converter import DataConverter


class TestDataConverter:
    """
    Test suite for the DataConverter class.
    This suite tests the conversion methods for both string to bytes and bytes to string,
    """

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        Setup method to initialize the DataConverter instance before each test.
        """
        self.converter = DataConverter()

    def test_convert_str_to_bytes_success(self):
        """
        Test the conversion of a string to bytes.
        """
        data = "Hello, World!"
        result = self.converter.convert_str_to_bytes(data)
        assert isinstance(result, bytes)
        assert result == b"Hello, World!"

    def test_convert_str_to_bytes_type_error(self):
        """
        Test that a TypeError is raised when the input is not a string.
        """
        with pytest.raises(TypeError) as exc_info:
            self.converter.convert_str_to_bytes(123)
        assert str(exc_info.value) == "Data must be a string."

    def test_convert_str_to_bytes_runtime_error(self, mocker):
        """
        Test that a RuntimeError is raised when the conversion fails.
        """
        mocker.patch.object(
            self.converter,
            "convert_str_to_bytes",
            side_effect=RuntimeError("Conversion error"),
        )
        with pytest.raises(RuntimeError):
            self.converter.convert_str_to_bytes("Hello, World!")

    def test_convert_bytes_to_str_success(self):
        """
        Test the conversion of bytes to a string.
        """
        data = b"Hello, World!"
        result = self.converter.convert_bytes_to_str(data)
        assert isinstance(result, str)
        assert result == "Hello, World!"

    def test_convert_bytes_to_str_type_error(self):
        """
        Test that a TypeError is raised when the input is not bytes.
        """
        with pytest.raises(TypeError) as exc_info:
            self.converter.convert_bytes_to_str("Not bytes")
        assert str(exc_info.value) == "Data must be bytes."

    def test_convert_bytes_to_str_runtime_error(self, mocker):
        """
        Test that a RuntimeError is raised when the conversion fails.
        """
        mocker.patch.object(
            self.converter,
            "convert_bytes_to_str",
            side_effect=RuntimeError("Conversion error"),
        )
        with pytest.raises(RuntimeError):
            self.converter.convert_bytes_to_str(b"Hello, World!")
