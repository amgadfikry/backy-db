# tests/io_engine/stream/test_stream_base.py
import pytest
from io_engine.stream.stream_base import StreamBase
from pathlib import Path


class TestStreamBase:
    """
    Test suite for the StreamBase class.
    This class tests the basic functionality of the StreamBase class.
    """

    @pytest.fixture
    def stream_base(self, mocker, tmp_path):
        """
        Fixture to create an instance of StreamBase for testing.
        This fixture will be used in all test methods.
        """
        self.file_path = tmp_path / "test_file.txt"
        self.file_path.touch()
        mocker.patch.object(StreamBase, "_identify_mode", return_value="wb")
        return StreamBase(file_path=self.file_path)

    def test_initialization(self, stream_base):
        """
        Test that StreamBase initializes correctly with a valid file path.
        """
        assert stream_base.file_path is not None
        assert stream_base.file_path.exists()
        assert stream_base.mode == "wb"
        assert isinstance(stream_base.file_path, Path)
        assert stream_base.stream is None

    def test_identify_mode_read_mode(self):
        """
        Test that the _identify_mode method correctly identifies the read mode.
        """

        class ReadStream(StreamBase):
            pass

        read_stream = ReadStream(Path("dummy_path"))
        mode = read_stream._identify_mode()
        assert mode == "rb"

    def test_identify_mode_write_mode(self):
        """
        Test that the _identify_mode method correctly identifies the write mode.
        """

        class WriteStream(StreamBase):
            pass

        write_stream = WriteStream(Path("dummy_path"))
        mode = write_stream._identify_mode()
        assert mode == "wb"

    def test_identify_mode_unknown(self):
        """
        Test that the _identify_mode method raises an error for unknown stream types.
        """

        class UnknownStream(StreamBase):
            pass

        with pytest.raises(ValueError) as exc_info:
            UnknownStream(Path("dummy_path"))
        assert "Unknown stream type. Must be 'WriteStream' or 'ReadStream'." in str(
            exc_info.value
        )

    def test_open_stream_success(self, stream_base):
        """
        Test the open_stream method.
        This test checks if the stream opens correctly and returns a file object.
        """
        stream = stream_base.open_stream()
        assert stream is not None
        assert not stream.closed
        stream.write(b"Test data")
        stream.close()
        assert stream.closed
        assert self.file_path.read_bytes() == b"Test data"

    def test_open_stream_failure(self, mocker, stream_base):
        """
        Test the open_stream method when it fails to open the stream.
        This test checks if the method raises a RuntimeError when it cannot open the file.
        """
        mocker.patch("builtins.open", side_effect=IOError("File not found"))
        with pytest.raises(RuntimeError) as exc_info:
            stream_base.open_stream()
        assert "Could not open stream" in str(exc_info.value)

    def test_close_stream_success(self, stream_base):
        """
        Test the close_stream method.
        This test checks if the stream closes correctly without raising an error.
        """
        stream_base.open_stream()
        assert not stream_base.stream.closed
        stream_base.close_stream()
        assert stream_base.stream.closed

    def test_close_stream_failure(self, mocker, stream_base):
        """
        Test the close_stream method when it fails to close the stream.
        This test checks if the method raises a RuntimeError when it cannot close the stream.
        """
        stream_base.open_stream()
        mocker.patch.object(
            stream_base.stream, "close", side_effect=IOError("Close error")
        )
        with pytest.raises(RuntimeError) as exc_info:
            stream_base.close_stream()
        assert "Could not close stream" in str(exc_info.value)

    def test_context_manager(self, stream_base):
        """
        Test the context manager.
        This test checks if the context manager works correctly.
        """
        with stream_base as stream:
            assert stream is not None
            assert not stream.stream.closed
            assert stream.file_path.exists()
            assert stream.mode == "wb"
        assert stream.stream.closed
