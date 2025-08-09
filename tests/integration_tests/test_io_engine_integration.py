# tests/integration_tests/test_io_engine_integration.py
from io_engine.stream.read_stream import ReadStream
from io_engine.data_converter import DataConverter
from io_engine.stream.write_stream import WriteStream
from io_engine.io_creator import IOCreator
import pytest


class TestIOEngineIntegration:
    """
    Integration tests for the IO Engine components.
    This class tests the interaction between ReadStream, WriteStream, IOCreator, and DataConverter.
    It ensures that data can be written to a stream, converted, and read back correctly.
    """

    @pytest.fixture(autouse=True)
    def setup(self, mocker, tmp_path):
        """
        Fixture to set up the test environment.
        Creates a temporary file for testing and mocks necessary methods.
        """
        mocker.patch.object(
            IOCreator, "_generate_main_backup_path", return_value=tmp_path
        )
        self.data_converter = DataConverter()

    def test_create_back_file_write_bytes_then_read_bytes(self):
        """
        Test creating a Backy file, writing bytes to it, and then reading those bytes back.
        This test ensures that the data written can be read correctly.
        """
        backup_type = "backy"
        db_name = "test_db"
        feature_name = "test_feature"
        data = "This is a test data chunk."

        io_creator = IOCreator(backup_type, db_name)
        file_path = io_creator.create_file(feature_name)

        assert file_path.exists()

        # Write data to the stream
        with WriteStream(file_path) as writer:
            byte_data = self.data_converter.convert_str_to_bytes(data)
            writer.write_stream(feature_name, byte_data)

        # Read data from the stream
        with ReadStream(file_path) as reader:
            read_data = list(reader.read_stream())

        assert len(read_data) == 1
        assert read_data[0][0] == feature_name
        assert read_data[0][1] == byte_data
        assert self.data_converter.convert_bytes_to_str(read_data[0][1]) == data

    def test_create_sql_file_write_bytes_then_read_bytes_with_3_chunks(self):
        """
        Test creating a SQL file, writing bytes in three chunks, and then reading those bytes back.
        This test ensures that the data written in multiple chunks can be read correctly.
        """
        backup_type = "sql"
        db_name = "test_db_sql"
        feature_name = ["tables", "columns", "data"]
        data_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]

        io_creator = IOCreator(backup_type, db_name)
        file_path = io_creator.create_file(feature_name)

        assert file_path.exists()

        # Write data to the stream in chunks
        with WriteStream(file_path) as writer:
            for feature, chunk in zip(feature_name, data_chunks):
                byte_data = self.data_converter.convert_str_to_bytes(chunk)
                writer.write_stream(feature, byte_data)

        # Read data from the stream
        with ReadStream(file_path) as reader:
            read_data = list(reader.read_stream())

        assert len(read_data) == len(data_chunks)
        for i, chunk in enumerate(data_chunks):
            assert read_data[i][0] == feature_name[i]
            assert read_data[i][1] == self.data_converter.convert_str_to_bytes(chunk)
            assert self.data_converter.convert_bytes_to_str(read_data[i][1]) == chunk
