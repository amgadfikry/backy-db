# tests/security/kms/test_kms_base.py
from security.kms.aws_kms import AWSKMS
from botocore.exceptions import ClientError
import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
import boto3


class TestAWSKMS:
    """
    Test suite for the AWSKMS class.
    """

    @pytest.fixture
    def aws_kms(self, mocker):
        """
        Fixture to create an instance of AWSKMS.
        Returns:
            AWSKMS: An instance of AWSKMS.
        """
        mocker.patch("boto3.client", return_value=mocker.Mock())
        return AWSKMS()

    def test_generate_key_success(self, aws_kms, mocker):
        """
        Test the generate_key method of AWSKMS.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "create_key",
            return_value={"KeyMetadata": {"KeyId": "test-key-id"}},
        )
        mocker.patch.object(aws_kms, "_create_alias", return_value="alias/test-key-id")

        key_alias = aws_kms.generate_key("test-key-alias")

        assert key_alias == "alias/test-key-id"
        aws_kms.kms_client.create_key.assert_called_once_with(
            Description="Asymmetric key for BackyDB hybrid encryption",
            KeyUsage="ENCRYPT_DECRYPT",
            CustomerMasterKeySpec="RSA_4096",
            Origin="AWS_KMS",
        )
        assert aws_kms._create_alias.call_count == 1

    def test_generate_key_failure(self, aws_kms, mocker, caplog):
        """
        Test the generate_key method of AWSKMS when it fails.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "create_key",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "CreateKey",
            ),
        )

        with pytest.raises(RuntimeError) as excinfo:
            aws_kms.generate_key("test-key-alias")
        assert "Failed to create KMS key" in str(excinfo.value)
        assert "Failed to create KMS key" in caplog.text

    def test_get_public_key_success(self, aws_kms, mocker):
        """
        Test the get_public_key method of AWSKMS.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "get_public_key",
            return_value={"PublicKey": b"test-public-key"},
        )
        mocker.patch.object(
            aws_kms, "_convert_der_key_to_pem", return_value=b"test-public-key"
        )

        public_key = aws_kms.get_public_key("test-key-id")
        assert public_key == b"test-public-key"
        aws_kms.kms_client.get_public_key.assert_called_once_with(KeyId="test-key-id")

    def test_get_public_key_failure(self, aws_kms, mocker, caplog):
        """
        Test the get_public_key method of AWSKMS when it fails.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "get_public_key",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "GetPublicKey",
            ),
        )

        with pytest.raises(RuntimeError) as excinfo:
            aws_kms.get_public_key("test-key-id")
        assert "Failed to retrieve public key" in str(excinfo.value)
        assert "Failed to retrieve public key" in caplog.text

    def test_symetric_key_decryption_success(self, aws_kms, mocker):
        """
        Test the decrypt_symmetric_key method of AWSKMS.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "decrypt",
            return_value={"Plaintext": b"decrypted-symmetric-key"},
        )

        decrypted_key = aws_kms.decrypt_symmetric_key("test-key-id", b"encrypted-key")

        assert decrypted_key == b"decrypted-symmetric-key"
        aws_kms.kms_client.decrypt.assert_called_once_with(
            CiphertextBlob=b"encrypted-key",
            KeyId="test-key-id",
            EncryptionAlgorithm="RSAES_OAEP_SHA_256",
        )

    def test_symetric_key_decryption_no_encrypted_key(self, aws_kms, caplog):
        """
        Test the decrypt_symmetric_key method of AWSKMS with an empty encrypted key.
        """
        with pytest.raises(ValueError) as excinfo:
            aws_kms.decrypt_symmetric_key("test-key-id", b"")
        assert "Encrypted key is empty." in str(excinfo.value)
        assert "Encrypted key is empty." in caplog.text

    def test_symetric_key_decryption_failure(self, aws_kms, mocker, caplog):
        """
        Test the decrypt_symmetric_key method of AWSKMS when decryption fails.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "decrypt",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "Decrypt",
            ),
        )

        with pytest.raises(RuntimeError) as excinfo:
            aws_kms.decrypt_symmetric_key("test-key-id", b"encrypted-key")
        assert "Failed to decrypt symmetric key" in str(excinfo.value)
        assert "Failed to decrypt symmetric key" in caplog.text

    def test_validate_key_success(self, aws_kms, mocker):
        """
        Test the validate_key method of AWSKMS.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            return_value={
                "KeyMetadata": {"KeyId": "test-key-id", "KeyState": "Enabled"}
            },
        )
        is_valid = aws_kms.validate_key("test-key-id")
        assert is_valid == "test-key-id"

    def test_validate_key_not_found(self, aws_kms, mocker, caplog):
        """
        Test the validate_key method of AWSKMS when the key is not found.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            side_effect=ClientError(
                {"Error": {"Code": "NotFoundException", "Message": "Key not found"}},
                "DescribeKey",
            ),
        )
        is_valid = aws_kms.validate_key("test-key-id")
        assert is_valid is None
        assert "Failed to validate KMS key" in caplog.text

    def test_validate_key_disabled(self, aws_kms, mocker, caplog):
        """
        Test the validate_key method of AWSKMS when the key is disabled.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            return_value={
                "KeyMetadata": {"KeyId": "test-key-id", "KeyState": "Disabled"}
            },
        )
        is_valid = aws_kms.validate_key("test-key-id")
        assert is_valid is None
        assert "KMS key test-key-id exists but is not enabled." in caplog.text

    def test_validate_key_invalid_key_id(self, aws_kms, mocker, caplog):
        """
        Test the validate_key method of AWSKMS with an invalid key ID.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value=None)
        aws_kms.validate_key("key-id")
        assert "No key found for alias key-id." in caplog.text
        assert aws_kms.kms_client.describe_key.call_count == 0

    def test_delete_key_success(self, aws_kms, mocker):
        """
        Test the delete_key method of AWSKMS.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms, "_resolve_alias_to_key_id", return_value="test-key-id"
        )
        mocker.patch.object(
            aws_kms.kms_client, "schedule_key_deletion", return_value=None
        )

        aws_kms.delete_key("test-key-id")
        aws_kms.kms_client.schedule_key_deletion.assert_called_once_with(
            KeyId="test-key-id", PendingWindowInDays=7
        )

    def test_delete_key_failure(self, aws_kms, mocker, caplog):
        """
        Test the delete_key method of AWSKMS when deletion fails.
        """
        mocker.patch.object(aws_kms, "_get_key", return_value="test-key-id")
        mocker.patch.object(
            aws_kms, "_resolve_alias_to_key_id", return_value="test-key-id"
        )
        mocker.patch.object(
            aws_kms.kms_client,
            "schedule_key_deletion",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "ScheduleKeyDeletion",
            ),
        )

        with pytest.raises(RuntimeError) as excinfo:
            aws_kms.delete_key("test-key-id")
        assert "Failed to delete KMS key" in str(excinfo.value)
        assert "Failed to delete KMS key" in caplog.text

    def test_create_alias_success(self, aws_kms, mocker):
        """
        Test the _create_alias method of AWSKMS.
        """
        mocker.patch.object(aws_kms.kms_client, "create_alias", return_value=None)
        alias_name = aws_kms._create_alias("test-key-id", "test-alias")
        assert alias_name == "test-alias"
        aws_kms.kms_client.create_alias.assert_called_once_with(
            AliasName="alias/test-alias", TargetKeyId="test-key-id"
        )

    def test_create_alias_failure(self, aws_kms, mocker, caplog):
        """
        Test the _create_alias method of AWSKMS when alias creation fails.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "create_alias",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "CreateAlias",
            ),
        )

        with pytest.raises(RuntimeError) as excinfo:
            aws_kms._create_alias("test-key-id", "test-alias")
        assert "Failed to create alias" in str(excinfo.value)
        assert "Failed to create alias" in caplog.text

    def test_get_key_success_if_key_is_not_auto(self, aws_kms):
        """
        Test the _get_key method of AWSKMS when key_id is not 'auto'.
        """
        key_id = "test-key-id"
        key = aws_kms._get_key(key_id)
        assert key == f"alias/{key_id}"

    def test_get_key_success_if_key_is_auto(self, aws_kms, mocker):
        """
        Test the _get_key method of AWSKMS when key_id is 'auto'.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "list_aliases",
            return_value={
                "Aliases": [
                    {
                        "AliasName": "alias/backy_test-key-id",
                        "TargetKeyId": "test-key-id",
                    }
                ]
            },
        )
        key = aws_kms._get_key("auto")
        assert key == "alias/backy_test-key-id"

    def test_get_key_success_with_latest_version(self, aws_kms, mocker):
        """
        Test the _get_key method of AWSKMS with multiple aliases.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "list_aliases",
            return_value={
                "Aliases": [
                    {"AliasName": "alias/backy_v1", "TargetKeyId": "key-id-1"},
                    {"AliasName": "alias/backy_v2", "TargetKeyId": "key-id-2"},
                    {"AliasName": "alias/backy_v3", "TargetKeyId": "key-id-3"},
                ]
            },
        )
        key = aws_kms._get_key("auto")
        assert key == "alias/backy_v3"

    def test_get_key_no_current_aliases(self, aws_kms, mocker):
        """
        Test the _get_key method of AWSKMS when no current aliases are found.
        """
        mocker.patch.object(
            aws_kms.kms_client, "list_aliases", return_value={"Aliases": []}
        )
        key = aws_kms._get_key("auto")
        assert key is None

    def test_get_key_no_matching_aliases(self, aws_kms, mocker):
        """
        Test the _get_key method of AWSKMS when no matching aliases are found.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "list_aliases",
            return_value={
                "Aliases": [
                    {"AliasName": "alias/other_alias", "TargetKeyId": "other-key-id"}
                ]
            },
        )
        key = aws_kms._get_key("auto")
        assert key is None

    def test_get_key_failure(self, aws_kms, mocker, caplog):
        """
        Test the _get_key method of AWSKMS when an error occurs.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "list_aliases",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "ListAliases",
            ),
        )
        with pytest.raises(RuntimeError) as excinfo:
            aws_kms._get_key("auto")
        assert "Failed to resolve latest key" in str(excinfo.value)
        assert "Failed to resolve latest key" in caplog.text

    def test_convert_der_key_to_pem_success(self, aws_kms):
        """
        Test the _convert_der_key_to_pem method of AWSKMS.
        """
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        der_key = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        pem_result = aws_kms._convert_der_key_to_pem(der_key)
        assert pem_result.startswith(b"-----BEGIN PUBLIC KEY-----")
        loaded_key = serialization.load_pem_public_key(pem_result)
        assert loaded_key.public_numbers() == public_key.public_numbers()

    def test_convert_der_key_to_pem_failure(self, aws_kms, caplog):
        """
        Test the _convert_der_key_to_pem method of AWSKMS when conversion fails.
        """
        with pytest.raises(RuntimeError) as excinfo:
            aws_kms._convert_der_key_to_pem(b"invalid-der-key")
        assert "Failed to convert DER key to PEM" in str(excinfo.value)
        assert "Failed to convert DER key to PEM" in caplog.text

    def test_resolve_key_id_to_alias_success_with_alias_word(self, aws_kms, mocker):
        """
        Test the _resolve_alias_to_key_id method of AWSKMS.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            return_value={"KeyMetadata": {"KeyId": "test-key-id"}},
        )
        key_id = aws_kms._resolve_alias_to_key_id("alias/test-alias")
        assert key_id == "test-key-id"

    def test_resolve_key_id_to_alias_success_without_alias_word(self, aws_kms, mocker):
        """
        Test the _resolve_alias_to_key_id method of AWSKMS without 'alias/' prefix.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            return_value={"KeyMetadata": {"KeyId": "test-key-id"}},
        )
        key_id = aws_kms._resolve_alias_to_key_id("test-alias")
        assert key_id == "test-key-id"

    def test_resolve_key_id_to_alias_failure(self, aws_kms, mocker, caplog):
        """
        Test the _resolve_alias_to_key_id method of AWSKMS when resolving fails.
        """
        mocker.patch.object(
            aws_kms.kms_client,
            "describe_key",
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Server Error"}},
                "DescribeKey",
            ),
        )
        with pytest.raises(RuntimeError) as excinfo:
            aws_kms._resolve_alias_to_key_id("alias/test-alias")
        assert "Failed to resolve alias to key ID" in str(excinfo.value)
        assert "Failed to resolve alias to key ID" in caplog.text

    @pytest.fixture
    def live_aws_kms(self, monkeypatch):
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
        # random key name for testing
        key_name = "backy_test_key_test_1"
        return key_name, AWSKMS()

    @pytest.mark.usefixtures("require_localstack")
    def test_generate_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the generate_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        key_id = aws_kms.generate_key(key_name)
        assert key_id == key_name

    @pytest.mark.usefixtures("require_localstack")
    def test_get_public_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the get_public_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        public_key = aws_kms.get_public_key(key_name)
        assert isinstance(public_key, bytes)

    @pytest.mark.usefixtures("require_localstack")
    def test_decrypt_symmetric_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the decrypt_symmetric_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        public_key = aws_kms.get_public_key(key_name)
        assert isinstance(public_key, bytes)

        symmetric_key = AESGCM.generate_key(bit_length=256)
        public_key_obj = serialization.load_pem_public_key(public_key)
        encrypted_symmetric_key = public_key_obj.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        decrypted_data = aws_kms.decrypt_symmetric_key(
            key_name, encrypted_symmetric_key
        )
        assert decrypted_data == symmetric_key

    @pytest.mark.usefixtures("require_localstack")
    def test_validate_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the validate_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        is_valid = aws_kms.validate_key(key_name)
        assert is_valid == key_name

    @pytest.mark.usefixtures("require_localstack")
    def test_get_latest_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the _get_latest_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        latest = "backy_test_key_test_2"
        key_id = aws_kms.generate_key(latest)
        assert latest == key_id
        key = aws_kms._get_key("auto")
        assert key != f"alias/{key_name}"

    @pytest.mark.usefixtures("require_localstack")
    def test_delete_key_with_aws_credentials(self, live_aws_kms, caplog):
        """
        Test the delete_key method of AWSKMS with AWS credentials.
        This test will only run if AWS credentials are set.
        """
        key_name, aws_kms = live_aws_kms
        aws_kms.delete_key(key_name)
        with pytest.raises(Exception):
            aws_kms.get_public_key(key_name)
