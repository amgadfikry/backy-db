# tests/security/key_store/test_google_key_store.py
import pytest
from security.key_store.google_key_store import GoogleKeyStore
from google.api_core.exceptions import AlreadyExists, NotFound


class TestGoogleKeyStore:
    """
    Test suite for GoogleKeyStore class.
    """

    @pytest.fixture
    def google_key_store(self, monkeypatch, mocker):
        """
        Fixture to create an instance of GoogleKeyStore with mocked dependencies.
        """
        # Mocking the Google Cloud client
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project-id")
        mocker.patch(
            "google.cloud.secretmanager.SecretManagerServiceClient", mocker.Mock()
        )
        return GoogleKeyStore()

    def test_initialization(self, google_key_store, mocker):
        """
        Test the initialization of GoogleKeyStore.
        """
        assert google_key_store.project_id == "test-project-id"
        assert google_key_store.client is not None
        assert isinstance(google_key_store.client, mocker.Mock)

    def test_save_key_success(self, google_key_store, mocker):
        """
        Test saving a key successfully.
        """
        key_id = "test-key"
        key_data = b"test-data"
        mock_create_secret = mocker.patch.object(
            google_key_store.client, "create_secret", return_value=None
        )
        mock_add_version = mocker.patch.object(
            google_key_store.client, "add_secret_version", return_value=None
        )

        google_key_store.save_key(key_id, key_data)

        mock_create_secret.assert_called_once_with(
            request={
                "parent": f"projects/{google_key_store.project_id}",
                "secret_id": "backy_secret_key",
                "secret": {"replication": {"automatic": {}}},
            }
        )
        mock_add_version.assert_called_once_with(
            request={
                "parent": f"projects/{google_key_store.project_id}/secrets/backy_secret_key",
                "payload": {"data": key_data},
            }
        )

    def test_save_key_already_exists(self, google_key_store, mocker):
        """
        Test saving a key when the secret already exists.
        """
        key_id = "test-key"
        key_data = b"test-data"
        mock_create_secret = mocker.patch.object(
            google_key_store.client,
            "create_secret",
            side_effect=AlreadyExists("Secret already exists"),
        )
        mock_add_version = mocker.patch.object(
            google_key_store.client, "add_secret_version", return_value=None
        )

        google_key_store.save_key(key_id, key_data)

        mock_create_secret.assert_called_once()
        mock_add_version.assert_called_once_with(
            request={
                "parent": f"projects/{google_key_store.project_id}/secrets/backy_secret_key",
                "payload": {"data": key_data},
            }
        )

    def test_save_key_failure_create_secret(self, google_key_store, mocker):
        """
        Test saving a key when there is an error creating the secret.
        """
        key_id = "test-key"
        key_data = b"test-data"
        mock_create_secret = mocker.patch.object(
            google_key_store.client,
            "create_secret",
            side_effect=Exception("Failed to create secret"),
        )

        with pytest.raises(RuntimeError) as exc_info:
            google_key_store.save_key(key_id, key_data)
        mock_create_secret.assert_called_once()
        assert str(exc_info.value) == "Failed to create secret backy_secret_key in GCP"

    def test_save_key_failure_add_version(self, google_key_store, mocker):
        """
        Test saving a key when there is an error adding a new version.
        """
        key_id = "test-key"
        key_data = b"test-data"
        mock_create_secret = mocker.patch.object(
            google_key_store.client, "create_secret", return_value=None
        )
        mock_add_version = mocker.patch.object(
            google_key_store.client,
            "add_secret_version",
            side_effect=Exception("Failed to add secret version"),
        )

        with pytest.raises(RuntimeError) as exc_info:
            google_key_store.save_key(key_id, key_data)
        mock_create_secret.assert_called_once()
        mock_add_version.assert_called_once()
        assert "Failed to save key to GCP: Failed to add secret version" in str(
            exc_info.value
        )

    def test_load_key_success(self, google_key_store, mocker):
        """
        Test loading a key successfully.
        """
        key_id = "backey_secret_key_2"
        expected_data = b"test-data"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/2",
        )
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "access_secret_version",
            return_value=mocker.Mock(payload=mocker.Mock(data=expected_data)),
        )

        result = google_key_store.load_key(key_id)

        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert result == expected_data

    def test_load_key_not_found(self, google_key_store, mocker):
        """
        Test loading a key that does not exist.
        """
        key_id = "non_existent_key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "access_secret_version",
            side_effect=NotFound("Secret version not found"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            google_key_store.load_key(key_id)
        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert f"Key {key_id} not found in GCP Secret Manager." in str(exc_info.value)

    def test_load_key_failure(self, google_key_store, mocker):
        """
        Test loading a key when there is an error during the load operation.
        """
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "access_secret_version",
            side_effect=Exception("Failed to access secret version"),
        )

        with pytest.raises(RuntimeError) as exc_info:
            google_key_store.load_key(key_id)
        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert f"Failed to load key {key_id}: Failed to access secret version" in str(
            exc_info.value
        )

    def test_delete_key_success(self, google_key_store, mocker, caplog):
        """
        Test deleting a key successfully.
        """
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_delete_secret = mocker.patch.object(
            google_key_store.client, "destroy_secret_version", return_value=None
        )

        google_key_store.delete_key(key_id)

        mock_delete_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )

    def test_delete_key_not_found(self, google_key_store, mocker):
        """
        Test deleting a key that does not exist.
        """
        key_id = "non_existent_key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_delete_secret = mocker.patch.object(
            google_key_store.client,
            "destroy_secret_version",
            side_effect=NotFound("Secret not found"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            google_key_store.delete_key(key_id)
        mock_delete_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert f"Key {key_id} not found in GCP Secret Manager." in str(exc_info.value)

    def test_delete_key_failure(self, google_key_store, mocker):
        """
        Test deleting a key when there is an error during the delete operation.
        """
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_delete_secret = mocker.patch.object(
            google_key_store.client,
            "destroy_secret_version",
            side_effect=Exception("Failed to delete secret"),
        )

        with pytest.raises(RuntimeError) as exc_info:
            google_key_store.delete_key(key_id)
        mock_delete_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert f"Failed to delete key {key_id}: Failed to delete secret" in str(
            exc_info.value
        )

    def test_validate_key_success(self, google_key_store, mocker):
        """
        Test validating a key that exists.
        """
        google_key_store.project_id = "test-project-id"
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_secret_version = mocker.Mock()
        mock_secret_version.state.name = "ENABLED"
        mock_secret_version.name = "backy/secret_key/versions/1"
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "get_secret_version",
            return_value=mock_secret_version,
        )

        result = google_key_store.validate_key(key_id)

        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert result == "backy_secret_key_1"

    def test_validate_key_no_project_id(self, google_key_store, caplog):
        """
        Test validating a key when the project ID is not set.
        """
        google_key_store.project_id = None
        result = google_key_store.validate_key("test-key")
        assert result is None
        assert "GCP_PROJECT_ID is not set in the environment variables." in caplog.text

    def test_validate_key_not_found(self, google_key_store, mocker):
        """
        Test validating a key that does not exist.
        """
        key_id = "non_existent_key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "get_secret_version",
            side_effect=NotFound("Secret not found"),
        )

        result = google_key_store.validate_key(key_id)

        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert result is None

    def test_validate_key_destroyed(self, google_key_store, mocker):
        """
        Test validating a key that is destroyed.
        """
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_state = mocker.Mock()
        mock_state.name = "DESTROYED"
        mock_response = mocker.Mock()
        mock_response.state = mock_state
        mock_get_secret = mocker.patch.object(
            google_key_store.client, "get_secret_version", return_value=mock_response
        )

        result = google_key_store.validate_key(key_id)

        mock_get_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert result is None

    def test_validate_key_failure(self, google_key_store, mocker):
        """
        Test validating a key when there is an error during the validation operation.
        """
        key_id = "test-key"
        mocker.patch.object(
            google_key_store,
            "_secret_path",
            return_value=f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1",
        )
        mock_access_secret = mocker.patch.object(
            google_key_store.client,
            "get_secret_version",
            side_effect=Exception("Failed to get secret"),
        )

        result = google_key_store.validate_key(key_id)

        mock_access_secret.assert_called_once_with(
            name=google_key_store._secret_path(key_id)
        )
        assert result is None

    def test_secret_path_with_specific_key_id(self, google_key_store):
        """
        Test the _secret_path method with a specific key ID.
        """
        key_id = "backey_secret_key_1"
        expected_path = f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/1"
        assert google_key_store._secret_path(key_id) == expected_path

    def test_secret_path_with_default_key_id(self, google_key_store):
        """
        Test the _secret_path method with the default key ID.
        """
        key_id = "auto"
        expected_path = f"projects/{google_key_store.project_id}/secrets/backy_secret_key/versions/latest"
        assert google_key_store._secret_path(key_id) == expected_path

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_save_keys_with_gcp_credentials(self, caplog):
        """
        Test saving keys with GCP credentials.
        This test will only run if the GCP credentials are set.
        """
        key_id = "backy_secret_key_1"
        key_data = b"test-data"
        google_key_store = GoogleKeyStore()
        google_key_store.save_key(key_id, key_data)

        assert "Secret backy_secret_key created in GCP Secret Manager." in caplog.text
        assert "Key saved as new version in Secret Manager." in caplog.text

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_validate_keys_with_gcp_credentials(self, caplog):
        """
        Test validating keys with GCP credentials.
        This test will only run if the GCP credentials are set.
        """
        key_id = "backy_secret_key_1"
        google_key_store = GoogleKeyStore()
        exists = google_key_store.validate_key(key_id)

        assert exists == "backy_secret_key_1"
        assert f"Key {key_id} exists in GCP Secret Manager." in caplog.text

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_load_keys_with_gcp_credentials(self, caplog):
        """
        Test loading keys with GCP credentials.
        This test will only run if the GCP credentials are set.
        """
        key_id = "backy_secret_key_1"
        google_key_store = GoogleKeyStore()
        data = google_key_store.load_key(key_id)

        assert isinstance(data, bytes)
        assert f"Key {key_id} loaded from GCP Secret Manager." in caplog.text
        assert data == b"test-data"

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_add_new_version_and_get_it(self, caplog):
        """
        Test adding a new version of a key and retrieving it.
        This test will only run if the GCP credentials are set.
        """
        key_id = "backy_secret_key_2"
        key_data = b"new-test-data"
        google_key_store = GoogleKeyStore()
        google_key_store.save_key(key_id, key_data)
        data = google_key_store.load_key(key_id)

        assert data == key_data
        latest = google_key_store.load_key("auto")

        assert latest == key_data
        assert latest != b"test-data"

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_delete_keys_with_gcp_credentials(self, caplog):
        """
        Test deleting keys with GCP credentials.
        This test will only run if the GCP credentials are set.
        """
        key_id = "backy_secret_key_2"
        google_key_store = GoogleKeyStore()
        google_key_store.delete_key(key_id)
        assert f"Key {key_id} deleted from GCP Secret Manager." in caplog.text
        assert google_key_store.validate_key(key_id) is None

        key_id = "backy_secret_key_1"
        google_key_store.delete_key(key_id)
        assert f"Key {key_id} deleted from GCP Secret Manager." in caplog.text
        assert google_key_store.validate_key(key_id) is None

        google_key_store.client.delete_secret(
            name=f"projects/{google_key_store.project_id}/secrets/backy_secret_key"
        )
