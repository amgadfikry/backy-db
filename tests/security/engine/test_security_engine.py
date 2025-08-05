# tests/security/engine/test_security_engine.py
from security.engine.security_engine import SecurityEngine
import pytest
from security.engine.key_generator import KeyGenerator
from security.engine.key_utils import KeyUtils


class TestSecurityEngine:
    """
    Test suite for the SecurityEngine class.
    This class contains tests for all methods in the SecurityEngine class,
    ensuring that key management operations are performed correctly.
    """

    @pytest.fixture
    def engine(self, tmp_path, mocker):
        """
        Fixture to create a SecurityEngine instance with a mock configuration.
        """
        # Create a temporary encryption file
        encryption_file = tmp_path / "encryption_file.enc"
        encryption_file.touch()
        # Mocking the dependencies (KeyGenerator, KeyUtils, KeyStoreManager, KMSManager)
        mocker.patch(
            "security.engine.security_engine.KeyGenerator", return_value=mocker.Mock()
        )
        mocker.patch(
            "security.engine.security_engine.KeyUtils", return_value=mocker.Mock()
        )
        mocker.patch(
            "security.engine.security_engine.KeyStoreManager",
            return_value=mocker.Mock(),
        )
        mocker.patch(
            "security.engine.security_engine.KMSManager", return_value=mocker.Mock()
        )
        # Mock the key management configuration
        config = {
            "type": "keystore",
            "provider": "local",
            "key_size": 4096,
            "key_version": None,
            "encryption_file": str(encryption_file),
        }
        # Create the SecurityEngine instance and assign the mocked manager
        engine = SecurityEngine(key_management_config=config)
        engine._assign_manager()
        return engine

    def test_security_engine_initialization(self, engine):
        """
        Test the initialization of the SecurityEngine.
        """
        assert engine.type == "keystore"
        assert engine.provider == "local"
        assert engine.key_size == 4096
        assert engine.key_version is None
        assert engine.encryption_file is not None
        assert engine.key_generator is not None
        assert engine.key_utils is not None
        assert not isinstance(engine.key_generator, KeyGenerator)
        assert not isinstance(engine.key_utils, KeyUtils)

    def test_assign_manager_keystore(self, engine):
        """
        Test the assignment of the key management manager for keystore type.
        """
        engine._assign_manager()
        assert engine.manager is not None

    def test_assign_manager_kms(self, engine):
        """
        Test the assignment of the key management manager for KMS type.
        """
        engine.type = "kms"
        engine._assign_manager()
        assert engine.manager is not None

    def test_assign_manager_invalid_type(self, engine, caplog):
        """
        Test the assignment of the key management manager with an invalid type.
        """
        engine.type = "invalid_type"
        with pytest.raises(
            ValueError, match="Unsupported key management type: invalid_type"
        ):
            engine._assign_manager()
        assert f"Unsupported key management type: {engine.type}" in caplog.text

    def test_generate_key_id_with_version_and_existing_key(self, engine, mocker):
        """
        Test the generation of a key ID with a specific version when the key already exists.
        """
        engine.key_version = "11"
        # Mock the validate_key method to return True for the existing key
        mocker.patch.object(
            engine.manager, "validate_key", return_value="backy_secret_key_11"
        )
        existing, key_id, key_identifier = engine._generate_key_id_and_check_it()
        assert existing is True
        assert key_id == "backy_secret_key_11"
        assert key_identifier == "backy_secret_key_11"

    def test_generate_key_id_with_version_and_non_existing_key_first(self, engine):
        """
        Test the generation of a key ID with a version when the key does not exist.
        """
        engine.key_version = "11"
        engine.manager.validate_key.side_effect = [None, "backy_secret_key_11"]
        existing, key_id, key_identifier = engine._generate_key_id_and_check_it()
        assert existing is True
        assert key_id == "auto"
        assert key_identifier == "backy_secret_key_11"

    def test_generate_key_id_with_version_and_non_existing_key_both(self, engine):
        """
        Test the generation of a key ID with a version when the key does not exist.
        """
        engine.key_version = "11"
        engine.manager.validate_key.side_effect = [None, None]
        existing, key_id, key_identifier = engine._generate_key_id_and_check_it()
        assert existing is False
        assert key_id == "backy_secret_key_1"
        assert key_identifier == "backy_secret_key_1"

    def test_generate_key_id_without_version_and_existing_key(self, engine, mocker):
        """
        Test the generation of a key ID without a version when the key exists.
        """
        engine.key_version = None
        mocker.patch.object(engine.manager, "validate_key", return_value="backy_123")
        existing, key_id, key_identifier = engine._generate_key_id_and_check_it()
        assert existing is True
        assert key_id == "auto"
        assert key_identifier == "backy_123"

    def test_generate_key_id_without_version_and_non_existing_key(self, engine):
        """
        Test the generation of a key ID without a version when the key does not exist.
        """
        engine.key_version = None
        engine.manager.validate_key.side_effect = [None, None]
        existing, key_id, key_identifier = engine._generate_key_id_and_check_it()
        assert existing is False
        assert key_id == "backy_secret_key_1"
        assert key_identifier == "backy_secret_key_1"

    def test_generate_private_keys_keystore(self, engine, mocker):
        """
        Test the generation of private keys for the keystore type.
        """
        engine.type = "keystore"
        # Mock the methods to generate and save the private key
        mocker.patch.object(
            engine.key_generator,
            "generate_rsa_private_key",
            return_value=b"some_private_key",
        )
        mocker.patch.object(engine.manager, "save_key")
        key_id = "test_key_id"

        engine._generate_private_keys(key_id)

        engine.key_generator.generate_rsa_private_key.assert_called_once_with(
            key_size=engine.key_size
        )
        engine.manager.save_key.assert_called_once_with(key_id, b"some_private_key")

    def test_generate_private_keys_kms(self, engine, mocker):
        """
        Test the generation of private keys for the KMS type.
        """
        engine.type = "kms"
        # Mock the method to generate the key using KMS
        mocker.patch.object(engine.manager, "generate_key")
        key_id = "test_key_id"
        engine._generate_private_keys(key_id)
        engine.manager.generate_key.assert_called_once_with(key_id)

    def test_get_public_key_keystore(self, engine, mocker):
        """
        Test the retrieval of the public key for the keystore type.
        """
        engine.type = "keystore"
        # Mock the methods to load the private key and extract the public key
        mocker.patch.object(
            engine.manager, "load_key", return_value=b"some_private_key"
        )
        mocker.patch.object(
            engine.key_generator, "extract_public_key", return_value=b"some_public_key"
        )
        key_id = "test_key_id"

        public_key = engine._get_public_key(key_id)

        assert public_key == b"some_public_key"
        engine.manager.load_key.assert_called_once_with(key_id)
        engine.key_generator.extract_public_key.assert_called_once_with(
            private_key=b"some_private_key"
        )

    def test_get_public_key_kms(self, engine, mocker):
        """
        Test the retrieval of the public key for the KMS type.
        """
        engine.type = "kms"
        # Mock the method to get the public key from the KMS
        mocker.patch.object(
            engine.manager, "get_public_key", return_value=b"some_public_key"
        )
        key_id = "test_key_id"
        public_key = engine._get_public_key(key_id)

        assert public_key == b"some_public_key"
        engine.manager.get_public_key.assert_called_once_with(key_id)

    def test_decrypt_symmetric_key_keystore(self, engine, mocker):
        """
        Test the decryption of the symmetric key for the keystore type.
        """
        engine.type = "keystore"
        # Mock the methods to load the private key and decrypt the symmetric key
        mocker.patch.object(
            engine.manager, "load_key", return_value=b"some_private_key"
        )
        mocker.patch.object(
            engine.key_utils,
            "decrypt_symmetric_key_with_private_key",
            return_value=b"some_symmetric_key",
        )
        key_id = "test_key_id"
        encrypted_key = b"some_encrypted_key"

        decrypted_key = engine._decrypt_symmetric_key(key_id, encrypted_key)

        assert decrypted_key == b"some_symmetric_key"
        engine.manager.load_key.assert_called_once_with(key_id)
        engine.key_utils.decrypt_symmetric_key_with_private_key.assert_called_once_with(
            b"some_private_key", encrypted_key
        )

    def test_decrypt_symmetric_key_kms(self, engine, mocker):
        """
        Test the decryption of the symmetric key for the KMS type.
        """
        engine.type = "kms"
        # Mock the method to decrypt the symmetric key using the KMS
        mocker.patch.object(
            engine.manager, "decrypt_symmetric_key", return_value=b"some_symmetric_key"
        )
        key_id = "test_key_id"
        encrypted_key = b"some_encrypted_key"

        decrypted_key = engine._decrypt_symmetric_key(key_id, encrypted_key)
        assert decrypted_key == b"some_symmetric_key"
        engine.manager.decrypt_symmetric_key.assert_called_once_with(
            key_id, encrypted_key
        )

    def test_handler_new_symmetric_key(self, engine, mocker):
        """
        Test the handling of a new symmetric key.
        """
        # Mock the methods to generate a symmetric key and encrypt it
        mocker.patch.object(
            engine.key_generator,
            "generate_symmetric_key",
            return_value=b"some_symmetric_key",
        )
        mocker.patch.object(
            engine.key_utils,
            "encrypt_symmetric_key_with_public_key",
            return_value=b"some_encrypted_key",
        )

        public_key = b"some_public_key"
        symmetric_key, encrypted_key = engine._handle_new_symmetric_key(public_key)
        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"

    def test_handle_existing_symmetric_key(self, engine, mocker):
        """
        Test the handling of an existing symmetric key.
        """
        # Mock the methods to read the encryption file and decrypt the symmetric key
        mocker.patch.object(
            engine.key_utils, "read_encryption_file", return_value=b"some_encrypted_key"
        )
        mocker.patch.object(
            engine, "_decrypt_symmetric_key", return_value=b"some_symmetric_key"
        )

        key_id = "test_key_id"
        symmetric_key, encrypted_key = engine._handle_existing_symmetric_key(key_id)
        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"

    def test_get_keys_success_with_exixting_key_and_symmetric_key(self, engine, mocker):
        """
        Test the retrieval of keys when an existing key and symmetric key are present.
        """
        key_id = "test_key_id"
        mocker.patch.object(engine, "_assign_manager")
        mocker.patch.object(
            engine, "_generate_key_id_and_check_it", return_value=(True, key_id, key_id)
        )
        mocker.patch.object(engine, "_generate_private_keys")
        mocker.patch.object(engine, "_get_public_key", return_value=b"some_public_key")
        mocker.patch.object(engine, "_handle_new_symmetric_key")
        mocker.patch.object(
            engine,
            "_handle_existing_symmetric_key",
            return_value=(b"some_symmetric_key", b"some_encrypted_key"),
        )

        symmetric_key, encrypted_key, key_id = engine.get_keys()

        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"
        assert key_id == "test_key_id"
        assert engine._assign_manager.called
        assert engine._generate_key_id_and_check_it.called
        assert not engine._generate_private_keys.called
        assert engine._get_public_key.called
        assert not engine._handle_new_symmetric_key.called
        assert engine._handle_existing_symmetric_key.called

    def test_get_keys_success_with_non_existing_key_and_symmetric_key(
        self, engine, mocker
    ):
        """
        Test the retrieval of keys when a non-existing key and symmetric key are present.
        """
        key_id = "test_key_id"
        mocker.patch.object(engine, "_assign_manager")
        mocker.patch.object(
            engine,
            "_generate_key_id_and_check_it",
            return_value=(False, key_id, key_id),
        )
        mocker.patch.object(engine, "_generate_private_keys")
        mocker.patch.object(engine, "_get_public_key", return_value=b"some_public_key")
        mocker.patch.object(engine, "_handle_new_symmetric_key")
        mocker.patch.object(
            engine,
            "_handle_existing_symmetric_key",
            return_value=(b"some_symmetric_key", b"some_encrypted_key"),
        )

        symmetric_key, encrypted_key, key_id = engine.get_keys()

        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"
        assert key_id == "test_key_id"
        assert engine._assign_manager.called
        assert engine._generate_key_id_and_check_it.called
        assert engine._generate_private_keys.called
        assert engine._get_public_key.called
        assert not engine._handle_new_symmetric_key.called
        assert engine._handle_existing_symmetric_key.called

    def test_get_keys_success_with_exist_key_and_non_existing_symmetric_key(
        self, engine, mocker
    ):
        """
        Test the retrieval of keys when an existing key and non-existing symmetric key are present.
        """
        key_id = "test_key_id"
        engine.encryption_file = None
        mocker.patch.object(engine, "_assign_manager")
        mocker.patch.object(
            engine, "_generate_key_id_and_check_it", return_value=(True, key_id, key_id)
        )
        mocker.patch.object(engine, "_generate_private_keys")
        mocker.patch.object(engine, "_get_public_key", return_value=b"some_public_key")
        mocker.patch.object(
            engine,
            "_handle_new_symmetric_key",
            return_value=(b"some_symmetric_key", b"some_encrypted_key"),
        )
        mocker.patch.object(engine, "_handle_existing_symmetric_key")

        symmetric_key, encrypted_key, key_id = engine.get_keys()

        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"
        assert key_id == "test_key_id"
        assert engine._assign_manager.called
        assert engine._generate_key_id_and_check_it.called
        assert not engine._generate_private_keys.called
        assert engine._get_public_key.called
        assert engine._handle_new_symmetric_key.called
        assert not engine._handle_existing_symmetric_key.called

    def test_get_keys_success_with_non_existing_key_and_non_existing_symmetric_key(
        self, engine, mocker
    ):
        """
        Test the retrieval of keys when a non-existing key and non-existing symmetric key are present.
        """
        key_id = "test_key_id"
        engine.encryption_file = None
        mocker.patch.object(engine, "_assign_manager")
        mocker.patch.object(
            engine,
            "_generate_key_id_and_check_it",
            return_value=(False, key_id, key_id),
        )
        mocker.patch.object(engine, "_generate_private_keys")
        mocker.patch.object(engine, "_get_public_key", return_value=b"some_public_key")
        mocker.patch.object(
            engine,
            "_handle_new_symmetric_key",
            return_value=(b"some_symmetric_key", b"some_encrypted_key"),
        )

        mocker.patch.object(engine, "_handle_existing_symmetric_key")

        symmetric_key, encrypted_key, key_id = engine.get_keys()
        assert symmetric_key == b"some_symmetric_key"
        assert encrypted_key == b"some_encrypted_key"
        assert key_id == "test_key_id"
        assert engine._assign_manager.called
        assert engine._generate_key_id_and_check_it.called
        assert engine._generate_private_keys.called
        assert engine._get_public_key.called
        assert engine._handle_new_symmetric_key.called
        assert not engine._handle_existing_symmetric_key.called

    def test_get_keys_error(self, engine, mocker):
        """
        Test the retrieval of keys when an error occurs.
        """
        mocker.patch.object(
            engine,
            "_assign_manager",
            side_effect=RuntimeError("Error during key generation"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            engine.get_keys()
        assert "Error retrieving keys" in str(exc_info.value)
