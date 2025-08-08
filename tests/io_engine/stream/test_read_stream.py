# tests/io_engine/stream/test_read_stream.py
from io_engine.stream.read_stream import ReadStream
import pytest
import json


class TestReadStream:
    """
    Test suite for the ReadStream class.
    This class tests the functionality of reading data from a stream.
    """

    @pytest.fixture(autouse=True)
    def read_stream(self, mocker, tmp_path):
        """
        Fixture to create an instance of ReadStream for testing.
        This fixture will be used in all test methods.
        """
        self.file_path = tmp_path / "test_read_stream.txt"
        self.file_path.touch()
        mocker.patch.object(ReadStream, "_identify_mode", return_value="rb")

    def test_read_stream_empty(self, caplog):
        """
        Test reading from an empty stream.
        Should log an info message and return without yielding any data.
        """
        # Empty the file to simulate an empty stream
        with open(self.file_path, "wb") as f:
            f.truncate(0)
        with ReadStream(self.file_path) as r:
            data = list(r.read_stream())
        assert data == []
        assert "No more data to read from stream" in caplog.text

    def test_read_stream_if_len_metadata_size_is_less_than_4(self, caplog):
        """
        Test reading from a stream where the metadata length is less than 4 bytes.
        Should raise an error and log an error message.
        """
        with open(self.file_path, "wb") as f:
            f.write(b"\x01\x02\x03")

        with ReadStream(self.file_path) as r:
            with pytest.raises(RuntimeError) as exc_info:
                list(r.read_stream())
        assert "Corrupted or incomplete metadata" in str(exc_info.value)
        assert "Metadata size is less than 4 bytes in stream" in caplog.text

    def test_read_stream_if_len_metadata_json_is_less_than_metadata_size(self, caplog):
        """
        Test reading from a stream where the metadata JSON length is less than the specified size.
        Should raise an error and log an error message.
        """
        with open(self.file_path, "wb") as f:
            f.write(
                len(
                    json.dumps({"feature_name": "test", "size": 5}).encode("utf-8")
                ).to_bytes(4, "big")
            )
            f.write(json.dumps({"feature_name": "test", "size": 5}).encode("utf-8")[:3])
            f.write(b"\x00\x00\x00\x05")

        with ReadStream(self.file_path) as r:
            with pytest.raises(RuntimeError) as exc_info:
                list(r.read_stream())
        assert "Corrupted or incomplete metadata" in str(exc_info.value)
        assert "Incomplete metadata read." in caplog.text

    def test_read_stream_if_len_data_is_less_than_its_size_in_metadata(self, caplog):
        """
        Test reading from a stream where the data length is less than the size specified in metadata.
        Should raise an error and log an error message.
        """
        with open(self.file_path, "wb") as f:
            f.write(
                len(
                    json.dumps({"feature_name": "test", "size": 5}).encode("utf-8")
                ).to_bytes(4, "big")
            )
            f.write(json.dumps({"feature_name": "test", "size": 5}).encode("utf-8"))
            f.write(b"\x00\x00\x00\x05")

        with ReadStream(self.file_path) as r:
            with pytest.raises(RuntimeError) as exc_info:
                list(r.read_stream())
        assert "Corrupted or incomplete data chunk" in str(exc_info.value)
        assert "Incomplete data chunk read." in caplog.text

    def test_read_stream_successful(self, caplog):
        """
        Test reading from a stream with valid data.
        Should yield the feature name and data correctly.
        """
        feature_name = "test_feature"
        data = b"test_data"
        metadata = {
            "feature_name": feature_name,
            "size": len(data),
        }

        with open(self.file_path, "wb") as f:
            metadata_bytes = json.dumps(metadata).encode("utf-8")
            metadata_length = len(metadata_bytes).to_bytes(4, "big")
            f.write(metadata_length + metadata_bytes + data)

        with ReadStream(self.file_path) as r:
            result = list(r.read_stream())

        assert len(result) == 1
        assert result[0] == (feature_name, data)

    def test_read_stream_error_handling(self, mocker, caplog):
        """
        Test error handling in read_stream method.
        Should log an error message and raise an exception.
        """

        with ReadStream(self.file_path) as r:
            mocker.patch.object(r, "stream", new_callable=mocker.PropertyMock)
            mocker.patch.object(r.stream, "read", side_effect=Exception("Read error"))
            with pytest.raises(Exception) as exc_info:
                list(r.read_stream())
        assert "Error reading data from stream" in caplog.text
        assert "Read error" in str(exc_info.value)

    def test_read_multiple_chunks_iterator(self):
        """
        Test reading multiple chunks from the stream.
        Should yield multiple feature names and data correctly.
        """
        feature_name1 = "feature1"
        data1 = b"data1"
        metadata1 = {
            "feature_name": feature_name1,
            "size": len(data1),
        }

        feature_name2 = "feature2"
        data2 = b"data2"
        metadata2 = {
            "feature_name": feature_name2,
            "size": len(data2),
        }

        with open(self.file_path, "wb") as f:
            metadata_bytes1 = json.dumps(metadata1).encode("utf-8")
            metadata_length1 = len(metadata_bytes1).to_bytes(4, "big")
            f.write(metadata_length1 + metadata_bytes1 + data1)

            metadata_bytes2 = json.dumps(metadata2).encode("utf-8")
            metadata_length2 = len(metadata_bytes2).to_bytes(4, "big")
            f.write(metadata_length2 + metadata_bytes2 + data2)

        with ReadStream(self.file_path) as r:
            result = list(r.read_stream())

        assert len(result) == 2
        assert result[0] == (feature_name1, data1)
        assert result[1] == (feature_name2, data2)
