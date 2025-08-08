# tests/io_engine/stream/write_stream.py
import os
from io_engine.stream.write_stream import WriteStream
import pytest
import json


class TestWriteStream:
    """
    Test suite for the WriteStream class.
    This class tests the functionality of writing data to a stream.
    """

    @pytest.fixture
    def write_stream(self, mocker, tmp_path):
        """
        Fixture to create an instance of WriteStream for testing.
        This fixture will be used in all test methods.
        """
        self.file_path = tmp_path / "test_write_stream.txt"
        self.file_path.touch()
        mocker.patch.object(WriteStream, "_identify_mode", return_value="wb")
        stream = open(self.file_path, "wb")
        write_stream = WriteStream(file_path=self.file_path)
        write_stream.stream = stream
        yield write_stream
        stream.close()

    def test_write_stream_success(self, write_stream):
        """
        Test that data can be written to the stream successfully.
        """
        feature_name = "tables"
        data = b"Test data for writing to stream."

        write_stream.write_stream(feature_name, data)
        write_stream.stream.flush()

        with open(self.file_path, "rb") as f:
            metadata_len = int.from_bytes(f.read(4), "big")
            metadata = json.loads(f.read(metadata_len))
            file_data = f.read()
        assert metadata["feature_name"] == feature_name
        assert metadata["size"] == len(data)
        assert file_data == data

    def test_write_stream_error(self, write_stream, mocker):
        """
        Test that an error is raised when writing to the stream fails.
        """
        mocker.patch.object(
            write_stream.stream, "write", side_effect=IOError("Write error")
        )
        feature_name = "tables"
        data = b"Test data for writing to stream."

        with pytest.raises(RuntimeError) as exc_info:
            write_stream.write_stream(feature_name, data)
        assert "Could not write data to stream" in str(exc_info.value)

    def test_write_stream_threshold(self, write_stream, mocker):
        """
        Test that the stream syncs to disk when the threshold is exceeded.
        """
        feature_name = "tables"
        data = b"x" * (write_stream.threshold + 1)
        mocker.patch.object(write_stream.stream, "flush")
        mocker.patch.object(write_stream.stream, "fileno", return_value=1)
        mocker.patch("os.fsync")
        write_stream.write_stream(feature_name, data)
        os.fsync.assert_called_once_with(write_stream.stream.fileno())
