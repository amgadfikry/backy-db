# tests/integration/test_security_integration.py
import pytest
from security.security_manager import SecurityManager
from security.key_store.google_key_store import GoogleKeyStore
from security.kms.aws_kms import AWSKMS
from pathlib import Path
import boto3


class TestSecurityIntegration:
    """
    Test suite for the SecurityManager class.
    This suite tests the integration of security operations such as encryption and decryption.
    """

    def test_encrypt_decrypt_bytes_using_local_key_store_first_time(
        self, monkeypatch, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with local provider
        """
        # Create a temporary directory for the local key store and set it as an environment variable
        local_key_store_path = tmp_path / "local_keystore"
        local_key_store_path.mkdir()
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", str(local_key_store_path))

        # Define the security configuration for the local key store and initialize the SecurityManager
        security_config = {
            "type": "keystore",
            "provider": "local",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)
        assert encrypted_data != data

        # encrypt again to ensure the key is reused and check the results
        encrypted_data2 = security_manager.encrypt_bytes(data)
        assert encrypted_data2 != encrypted_data

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data
        decrypted_data2 = security_manager.decrypt_bytes(encrypted_data2)
        assert decrypted_data2 == decrypted_data

    def test_encrypt_decrypt_bytes_using_local_key_store_specific_version(
        self, monkeypatch, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with local provider and specific version.
        """
        # Create a temporary directory for the local key store and set it as an environment variable
        local_key_store_path = tmp_path / "local_keystore"
        local_key_store_path.mkdir()
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", str(local_key_store_path))
        security_manager = SecurityManager({"type": "keystore", "provider": "local"})
        # Define the security configuration for the local key store with specific version
        security_config = {"type": "keystore", "provider": "local", "key_version": "1"}
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for specific version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

    def test_encrypt_decrypt_bytes_using_local_key_store_with_auto_version(
        self, monkeypatch, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with local provider and auto version.
        """
        # Create a temporary directory for the local key store and set it as an environment variable
        local_key_store_path = tmp_path / "local_keystore"
        local_key_store_path.mkdir()
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", str(local_key_store_path))

        # Create a first call to ensure the key is created
        security_manager = SecurityManager({"type": "keystore", "provider": "local"})

        # Define the security configuration for the local key store without specific version
        # This will use the latest version automatically
        security_config = {
            "type": "keystore",
            "provider": "local",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for auto version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert isinstance(encrypted_key, bytes)
        assert key_id is not None
        assert isinstance(key_id, str)
        assert key_id.startswith("backy_")
        assert Path(key_id).stem.split("_")[-1] == "1"

    def test_encrypt_decrypt_bytes_using_local_key_store_and_encrypted_key_file(
        self, monkeypatch, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with local provider and an encrypted key file.
        """
        # Create a temporary directory for the local key store and set it as an environment variable
        local_key_store_path = tmp_path / "local_keystore"
        local_key_store_path.mkdir()
        monkeypatch.setenv("LOCAL_KEY_STORE_PATH", str(local_key_store_path))

        # Create a temporary file for the encrypted key
        encrypted_key_file = tmp_path / "test_encrypted_key.pem"

        # Define the security configuration for the local key store using latest version
        security_config = {
            "type": "keystore",
            "provider": "local",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encrypted key file"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert key_id is not None

        # Save the encrypted key to the file
        with open(encrypted_key_file, "wb") as f:
            f.write(encrypted_key)

        # Define a new security configuration to load the encrypted key from the file with version with it
        security_config = {
            "type": "keystore",
            "provider": "local",
            "version": Path(key_id).stem.split("_")[-1],
            "encryption_file": str(encrypted_key_file),
        }
        security_manager = SecurityManager(security_config)

        # Get the encrypted key and key ID again to ensure they match
        _, key_id2 = security_manager.get_encrypted_key_and_key_id()
        assert key_id2 == key_id

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_encrypt_decrypt_bytes_using_gcp_key_store_first_time(self, tmp_path):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with gcp provider
        """
        # Define the security configuration for the gcp key store and initialize the SecurityManager
        security_config = {
            "type": "keystore",
            "provider": "google",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)
        assert encrypted_data != data

        # encrypt again to ensure the key is reused and check the results
        encrypted_data2 = security_manager.encrypt_bytes(data)
        assert encrypted_data2 != encrypted_data

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data
        decrypted_data2 = security_manager.decrypt_bytes(encrypted_data2)
        assert decrypted_data2 == decrypted_data

        # Remove the whole secret to ensure the next test starts fresh
        google_key_store = GoogleKeyStore()
        google_key_store.client.delete_secret(
            name=f"projects/{google_key_store.project_id}/secrets/backy_secret_key"
        )

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_encrypt_decrypt_bytes_using_gcp_key_store_specific_version(self, tmp_path):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with google provider and specific version.
        """
        # Call first to ensure the key is created
        security_manager = SecurityManager({"type": "keystore", "provider": "google"})
        # Define the security configuration for the local key store with specific version
        security_config = {"type": "keystore", "provider": "google", "key_version": "1"}
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for specific version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Remove the whole secret to ensure the next test starts fresh
        google_key_store = GoogleKeyStore()
        google_key_store.client.delete_secret(
            name=f"projects/{google_key_store.project_id}/secrets/backy_secret_key"
        )

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_encrypt_decrypt_bytes_using_gcp_key_store_with_auto_version(self):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with google provider and auto version.
        """
        # Create a first call to ensure the key is created
        security_manager = SecurityManager({"type": "keystore", "provider": "google"})
        # Define the security configuration for the google key store without specific version
        # This will use the latest version automatically
        security_config = {
            "type": "keystore",
            "provider": "google",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for auto version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert isinstance(encrypted_key, bytes)
        assert key_id is not None
        assert isinstance(key_id, str)
        assert key_id.startswith("backy_")
        assert Path(key_id).stem.split("_")[-1] == "1"

        # Remove the whole secret to ensure the next test starts fresh
        google_key_store = GoogleKeyStore()
        google_key_store.client.delete_secret(
            name=f"projects/{google_key_store.project_id}/secrets/backy_secret_key"
        )

    @pytest.mark.usefixtures("require_gcp_credentials")
    def test_encrypt_decrypt_bytes_using_gcp_key_store_and_encrypted_key_file(
        self, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        key_store type with google provider and an encrypted key file.
        """
        # Create a temporary file for the encrypted key
        encrypted_key_file = tmp_path / "test_encrypted_key.pem"

        # Define the security configuration for the google key store using latest version
        security_config = {
            "type": "keystore",
            "provider": "google",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encrypted key file"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert key_id is not None

        # Save the encrypted key to the file
        with open(encrypted_key_file, "wb") as f:
            f.write(encrypted_key)

        # Define a new security configuration to load the encrypted key from the file with version with it
        security_config = {
            "type": "keystore",
            "provider": "google",
            "version": Path(key_id).stem.split("_")[-1],
            "encryption_file": str(encrypted_key_file),
        }
        security_manager = SecurityManager(security_config)

        # Get the encrypted key and key ID again to ensure they match
        _, key_id2 = security_manager.get_encrypted_key_and_key_id()
        assert key_id2 == key_id

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Remove the whole secret to ensure the next test starts fresh
        google_key_store = GoogleKeyStore()
        google_key_store.client.delete_secret(
            name=f"projects/{google_key_store.project_id}/secrets/backy_secret_key"
        )

    @pytest.fixture
    def aws_kms(self, monkeypatch):
        """
        Fixture to create a live instance of AWSKMS for testing with actual AWS credentials.
        This will only run if AWS credentials are set in the environment.
        """
        # Set environment variables for AWS credentials
        monkeypatch.setenv("AWS_S3_BUCKET_NAME", "backy-backups")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        # Create a mock KMS client
        kms_client = boto3.client("kms", endpoint_url="http://localhost:4566")
        # Patch the boto3 client to use the mock KMS client
        monkeypatch.setattr("boto3.client", lambda *args, **kwargs: kms_client)

    @pytest.mark.usefixtures("require_localstack")
    def test_encrypt_decrypt_bytes_using_aws_kms_first_time(self, aws_kms):
        """
        This test verifies the encryption and decryption of bytes using
        kms type with aws provider
        """
        # Define the security configuration for the aws kms and initialize the SecurityManager
        security_config = {
            "type": "kms",
            "provider": "aws",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)
        assert encrypted_data != data

        # encrypt again to ensure the key is reused and check the results
        encrypted_data2 = security_manager.encrypt_bytes(data)
        assert encrypted_data2 != encrypted_data

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data
        decrypted_data2 = security_manager.decrypt_bytes(encrypted_data2)
        assert decrypted_data2 == decrypted_data

    @pytest.mark.usefixtures("require_localstack")
    def test_encrypt_decrypt_bytes_using_aws_kms_specific_version(self, aws_kms):
        """
        This test verifies the encryption and decryption of bytes using
        kms type with aws provider and specific version.
        """
        # Define the security configuration for the aws kms with specific version
        security_config = {"type": "kms", "provider": "aws", "key_version": "1"}
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for specific version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

    @pytest.mark.usefixtures("require_localstack")
    def test_encrypt_decrypt_bytes_using_aws_kms_with_auto_version(self, aws_kms):
        """
        This test verifies the encryption and decryption of bytes using
        kms type with aws provider and auto version.
        """
        # This will use the latest version automatically
        security_config = {
            "type": "kms",
            "provider": "aws",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for auto version encryption"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert isinstance(encrypted_key, bytes)
        assert key_id is not None
        assert isinstance(key_id, str)
        assert key_id.startswith("backy_")
        assert Path(key_id).stem.split("_")[-1] == "1"

    @pytest.mark.usefixtures("require_localstack")
    def test_encrypt_decrypt_bytes_using_aws_kms_and_encrypted_key_file(
        self, aws_kms, tmp_path
    ):
        """
        This test verifies the encryption and decryption of bytes using
        kms type with aws provider and an encrypted key file.
        """
        # Create a temporary file for the encrypted key
        encrypted_key_file = tmp_path / "test_encrypted_key.pem"

        # Define the security configuration for the aws kms using latest version
        security_config = {
            "type": "kms",
            "provider": "aws",
        }
        security_manager = SecurityManager(security_config)

        # Encrypt data and check the results
        data = b"Test data for encrypted key file"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data is not None

        # Get the encrypted key and key ID and check the results
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key is not None
        assert key_id is not None

        # Save the encrypted key to the file
        with open(encrypted_key_file, "wb") as f:
            f.write(encrypted_key)

        # Define a new security configuration to load the encrypted key from the file with version with it
        security_config = {
            "type": "kms",
            "provider": "aws",
            "version": Path(key_id).stem.split("_")[-1],
            "encryption_file": str(encrypted_key_file),
        }
        security_manager = SecurityManager(security_config)

        # Get the encrypted key and key ID again to ensure they match
        _, key_id2 = security_manager.get_encrypted_key_and_key_id()
        assert key_id2 == key_id

        # Decrypt the encrypted data and check the results
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data is not None
        assert isinstance(decrypted_data, bytes)
        assert decrypted_data == data

        # Remove the whole secret to ensure the next test starts fresh
        aws_kms = AWSKMS()
        aws_kms.delete_key(key_id)
