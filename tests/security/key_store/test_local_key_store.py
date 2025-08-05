# tests/key_store/test_local_key_store.py
import pytest
from security.key_store.local_key_store import LocalKeyStore
import os
from pathlib import Path


class TestLocalKeyStore:
    """
    Test suite for the LocalKeyStore class.
    This suite tests the key management operations of the local key store.
    """

    @pytest.fixture
    def local_key_store(self, monkeypatch, tmp_path):
        """
        Fixture to create an instance of LocalKeyStore.
        Returns:
            LocalKeyStore: An instance of LocalKeyStore.
        """
        # Set the environment variable for the local key store path
        secret_path = tmp_path / "test_keys"
        secret_path.mkdir(exist_ok=True)
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", str(secret_path))

        return LocalKeyStore()

    def test_initialization(self, local_key_store):
        """
        Test the initialization of LocalKeyStore.
        """
        assert local_key_store.store_path == os.getenv("LOCAL_KEY_STORE_PATH")
        assert isinstance(local_key_store, LocalKeyStore)

    def test_save_key_success(self, local_key_store, mocker):
        """
        Test the save_key method of LocalKeyStore.
        """
        key_path = Path(local_key_store.store_path) / "test-key-id.pem"
        key_id = "test-key-id"
        key_data = b"test_key_data"
        mocker.patch.object(local_key_store, "_get_key_path", return_value=key_path)

        local_key_store.save_key(key_id, key_data)

        assert key_path.exists()
        with open(key_path, "rb") as f:
            assert f.read() == key_data

    def test_save_key_failure(self, local_key_store, mocker):
        """
        Test the save_key method of LocalKeyStore when an error occurs.
        """
        key_id = "test-key-id"
        key_data = b"test_key_data"
        mocker.patch.object(
            local_key_store,
            "_get_key_path",
            return_value=Path("/invalid/path/test-key-id.pem"),
        )

        with pytest.raises(RuntimeError) as exc_info:
            local_key_store.save_key(key_id, key_data)
        assert "Failed to save key to local store" in str(exc_info.value)

    def test_load_key_success(self, local_key_store, mocker):
        """
        Test the load_key method of LocalKeyStore.
        """
        key_path = Path(local_key_store.store_path) / "test-key-id.pem"
        key_id = "test-key-id"
        key_data = b"test_key_data"
        key_path.write_bytes(key_data)
        mocker.patch.object(local_key_store, "_get_key_path", return_value=key_path)

        loaded_data = local_key_store.load_key(key_id)
        assert loaded_data == key_data

    def test_load_key_failure(self, local_key_store, mocker):
        """
        Test the load_key method of LocalKeyStore when the key does not exist.
        """
        key_id = "non-existent-key-id"
        mocker.patch.object(
            local_key_store,
            "_get_key_path",
            return_value=Path("/invalid/path/non-existent-key-id.pem"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            local_key_store.load_key(key_id)
        assert f"Key {key_id} not found in local store." in str(exc_info.value)

    def test_delete_key_success(self, local_key_store, mocker):
        """
        Test the delete_key method of LocalKeyStore.
        """
        key_path = Path(local_key_store.store_path) / "test-key-id.pem"
        key_id = "test-key-id"
        key_data = b"test_key_data"
        key_path.write_bytes(key_data)
        mocker.patch.object(local_key_store, "_get_key_path", return_value=key_path)

        local_key_store.delete_key(key_id)
        assert not key_path.exists()

    def test_delete_key_failure(self, local_key_store, mocker):
        """
        Test the delete_key method of LocalKeyStore when the key does not exist.
        """
        key_id = "non-existent-key-id"
        mocker.patch.object(
            local_key_store,
            "_get_key_path",
            return_value=Path("/invalid/path/non-existent-key-id.pem"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            local_key_store.delete_key(key_id)
        assert f"Key {key_id} not found in local store." in str(exc_info.value)

    def test_validate_key_success(self, local_key_store, mocker):
        """
        Test the validate_key method of LocalKeyStore.
        """
        key_path = Path(local_key_store.store_path) / "test-key-id.pem"
        key_id = "test-key-id"
        key_path.touch()
        mocker.patch.object(local_key_store, "_get_key_path", return_value=key_path)
        assert local_key_store.validate_key(key_id) == "test-key-id"

    def test_validate_key_no_store_path(self, monkeypatch, caplog):
        """
        Test the validate_key method of LocalKeyStore when store_path is not set.
        """
        monkeypatch.delenv("LOCAL_KEY_STORE_PATH", raising=False)
        local_key_store = LocalKeyStore()
        result = local_key_store.validate_key("test-key-id")
        assert result is None
        assert (
            "Key store path is not set (LOCAL_KEY_STORE_PATH missing)." in caplog.text
        )

    def test_validate_key_store_path_not_exist(self, local_key_store, caplog):
        """
        Test the validate_key method of LocalKeyStore when store_path does not exist.
        """
        local_key_store.store_path = "/invalid/path"
        result = local_key_store.validate_key("test-key-id")
        assert result is None
        assert (
            f"Key store path {local_key_store.store_path} does not exist."
            in caplog.text
        )

    def test_validate_key_file_not_dir(self, local_key_store, caplog):
        """
        Test the validate_key method of LocalKeyStore when store_path is not a directory.
        """
        key_path = Path(local_key_store.store_path) / "test-key-id.pem"
        key_path.touch()
        local_key_store.store_path = str(key_path)
        result = local_key_store.validate_key("test-key-id")
        assert result is None
        assert (
            f"Key store path {local_key_store.store_path} is not a directory."
            in caplog.text
        )

    def test_validate_key_file_not_writable(self, local_key_store, caplog):
        """
        Test the validate_key method of LocalKeyStore when store_path is not writable.
        """
        os.chmod(local_key_store.store_path, 0o444)
        result = local_key_store.validate_key("test-key-id")
        assert result is None
        assert (
            f"Key store path {local_key_store.store_path} is not writable."
            in caplog.text
        )

    def test_validate_key_file_not_exist(self, local_key_store, caplog, mocker):
        """
        Test the validate_key method of LocalKeyStore when the key file does not exist.
        """
        key_id = "non-existent-key-id"
        mocker.patch.object(
            local_key_store,
            "_get_key_path",
            return_value=Path("/invalid/path/non-existent-key-id.pem"),
        )
        result = local_key_store.validate_key(key_id)
        assert result is None
        assert f"Key {key_id} does not exist in local store." in caplog.text

    def test_get_key_path_success_with_existing_key(self, local_key_store):
        """
        Test the _get_key_path method of LocalKeyStore with an existing key.
        """
        key_id = "existing-key-id"
        key_path = Path(local_key_store.store_path) / f"{key_id}.pem"
        key_path.touch()
        result = local_key_store._get_key_path(key_id)
        assert result == key_path

    def test_get_key_path_success_with_auto_key(self, local_key_store, mocker):
        """
        Test the _get_key_path method of LocalKeyStore with 'auto' key.
        """
        key_id = "auto"
        key_path = Path(local_key_store.store_path) / "backy_20231001.pem"
        key_path.touch()
        mocker.patch.object(Path, "glob", return_value=[key_path])
        result = local_key_store._get_key_path(key_id)
        assert result == key_path

    def test_get_key_path_success_with_multiple_auto_keys(
        self, local_key_store, mocker
    ):
        """
        Test the _get_key_path method of LocalKeyStore with multiple 'auto' keys.
        """
        key_id = "auto"
        key_paths = [
            Path(local_key_store.store_path) / "backy_20231001.pem",
            Path(local_key_store.store_path) / "backy_20231002.pem",
        ]
        for path in key_paths:
            path.touch()

        mocker.patch.object(Path, "glob", return_value=key_paths)
        result = local_key_store._get_key_path(key_id)
        assert result == key_paths[1]

    def test_get_key_path_failure_with_no_auto_keys(self, local_key_store, mocker):
        """
        Test the _get_key_path method of LocalKeyStore when no keys are found for 'auto'.
        """
        key_id = "auto"
        mocker.patch.object(Path, "glob", return_value=[])
        assert local_key_store._get_key_path(key_id) is None
