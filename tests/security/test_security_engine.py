# tests/security/test_security_engine.py
import pytest
from unittest.mock import Mock
from security.security_engine import SecurityEngine
import shutil
import logging
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class TestSecurityEngine:
    """
    Tests for the SecurityEngine class.
    """

    @pytest.fixture
    def security_engine_setup(self, tmp_path, monkeypatch):
        """
        Setup fixture for SecurityEngine tests.
        """
        mock_main_backup_path = tmp_path / "test_backup"
        mock_main_backup_path.mkdir()
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(mock_main_backup_path))
        # Security configuration for the engine
        config = {
            "private_key_password": "test_password",
            "private_key_size": "2048",
            "integrity_password": "test_integrity_password",
            "integrity_check": True,
            "compression_extension": ".zip",
        }
        yield config, mock_main_backup_path
        # Cleanup after tests
        shutil.rmtree(mock_main_backup_path, ignore_errors=True)
        shutil.rmtree(
            mock_main_backup_path.parent / ".backy-secrets", ignore_errors=True
        )

    def test_init_success(self, security_engine_setup, monkeypatch):
        """
        Test that SecurityEngine initializes successfully with valid configuration.
        """
        config, _ = security_engine_setup
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: True)
        monkeypatch.setattr(
            SecurityEngine, "_load_public_key", lambda self: ("key", "v1")
        )
        engine = SecurityEngine(config)
        assert engine.password == "test_password"
        assert engine.private_key_size == "2048"
        assert engine.integrity_password == "test_integrity_password"
        assert engine.integrity_check is True
        assert engine.compression_extension == ".zip"
        assert engine.processing_path.exists()
        assert engine.secret_path.exists()
        assert engine.secret_path.is_dir()
        assert engine.secret_path == engine.processing_path.parent / ".backy-secrets"
        assert engine.public_key is not None
        assert engine.version == "v1"

    def test_init_no_main_backup_path(self, security_engine_setup, monkeypatch, caplog):
        """
        Test that SecurityEngine raises EnvironmentError if MAIN_BACKUP_PATH is not set.
        """
        config, _ = security_engine_setup
        monkeypatch.delenv("MAIN_BACKUP_PATH", raising=False)
        with caplog.at_level("ERROR"):
            with pytest.raises(EnvironmentError) as excinfo:
                SecurityEngine(config)
            assert "MAIN_BACKUP_PATH environment variable is not set." in str(
                excinfo.value
            )
            assert "MAIN_BACKUP_PATH environment variable is not set." in caplog.text

    def test_init_not_have_keys(self, security_engine_setup, monkeypatch):
        """
        Test that SecurityEngine generates keys if they do not exist.
        """
        config, _ = security_engine_setup
        # Mock _check_keys_exist to return False to trigger key generation
        mock_create_keys = Mock(return_value=True)
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: False)
        monkeypatch.setattr(
            SecurityEngine, "_generate_pub_and_priv_key", mock_create_keys
        )
        monkeypatch.setattr(
            SecurityEngine, "_load_public_key", lambda self: ("key", "v1")
        )
        engine = SecurityEngine(config)
        mock_create_keys.assert_called_once()
        assert engine.public_key is not None
        assert engine.version == "v1"

    def test_check_two_keys_exist_method(
        self, security_engine_setup, caplog, monkeypatch
    ):
        """
        Test __check_keys_exist returns True when keys exist.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        secret_path.mkdir(exist_ok=True)
        # Create dummy key files to simulate existing keys
        (secret_path / "private_key_v1.pem").touch()
        (secret_path / "public_key_v1.pem").touch()
        # Directly call the private method for testing purposes
        monkeypatch.setattr(
            SecurityEngine, "_load_public_key", lambda self: ("key", "v1")
        )
        engine = SecurityEngine(config)
        with caplog.at_level("INFO"):
            assert engine._check_keys_exist() is True
            assert (
                "Public and private key files found in the secret path" in caplog.text
            )

    def test_check_two_keys_not_exist_method(
        self, security_engine_setup, monkeypatch, caplog
    ):
        """
        Test __check_keys_exist returns False when keys do not exist.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        secret_path.mkdir(exist_ok=True)
        # Directly call the private method for testing purposes
        mock_create_keys = Mock(return_value=True)
        monkeypatch.setattr(
            SecurityEngine, "_load_public_key", lambda self: ("key", "v1")
        )
        monkeypatch.setattr(
            SecurityEngine, "_generate_pub_and_priv_key", mock_create_keys
        )
        with caplog.at_level("INFO"):
            engine = SecurityEngine(config)
            assert engine._check_keys_exist() is False
            assert (
                "No public or private key files found in the secret path" in caplog.text
            )

    def test_generate_pub_and_priv_key_success(
        self, security_engine_setup, monkeypatch
    ):
        """
        Test that public and private keys are generated successfully.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        # Ensure _check_keys_exist returns False to trigger generation
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: False)
        monkeypatch.setattr(
            SecurityEngine, "_load_public_key", lambda self: ("key", "v1")
        )
        engine = SecurityEngine(config)
        engine._generate_pub_and_priv_key()
        private_key_files = list(secret_path.glob("private_key_*.pem"))
        public_key_files = list(secret_path.glob("public_key_*.pem"))
        assert len(private_key_files) == 1
        assert len(public_key_files) == 1
        assert private_key_files[0].name == "private_key_v1.pem"
        assert public_key_files[0].name == "public_key_v1.pem"

    def test_generate_pub_and_priv_key_failure(
        self, security_engine_setup, monkeypatch, mocker, caplog
    ):
        """
        Test that generate_pub_and_priv_key handles errors during key generation.
        """
        config, _ = security_engine_setup
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: False)
        mocker.patch(
            "security.security_engine.rsa.generate_private_key",
            side_effect=Exception("Mock key gen error"),
        )
        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                SecurityEngine(config)
            assert "Failed to generate public and private keys" in str(excinfo.value)
            assert (
                "Error generating public and private keys: Mock key gen error"
                in caplog.text
            )

    def test_load_public_key_success(self, security_engine_setup, monkeypatch):
        """
        Test that the latest public key is loaded successfully.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        secret_path.mkdir(exist_ok=True)
        # Create dummy public key files for testing sorting and loading
        # Old version
        old_key_path = secret_path / "public_key_v1.pem"
        with open(old_key_path, "wb") as f:
            f.write(
                rsa.generate_private_key(public_exponent=65537, key_size=2048)
                .public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
        # Latest version
        latest_key_path = secret_path / "public_key_v2.pem"
        with open(latest_key_path, "wb") as f:
            f.write(
                rsa.generate_private_key(public_exponent=65537, key_size=2048)
                .public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
        # Ensure _check_keys_exist returns True to trigger loading
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: True)
        # Mock private key generation to avoid file operations during init that interfere with this test.
        engine = SecurityEngine(config)
        assert engine.public_key is not None
        assert engine.version == "v2"

    def test_load_public_key_file_not_found(
        self, security_engine_setup, monkeypatch, caplog
    ):
        """
        Test that load_public_key raises FileNotFoundError if no public key file is found.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        secret_path.mkdir(exist_ok=True)
        # Ensure _check_keys_exist returns True to trigger loading
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: True)
        #
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError) as excinfo:
                SecurityEngine(config)
            assert "No public key file found in the secret path." in str(excinfo.value)
            assert "No public key file found in the secret path." in caplog.text

    def test_load_public_key_failure(
        self, security_engine_setup, monkeypatch, caplog, mocker
    ):
        """
        Test that load_public_key handles errors during public key loading.
        """
        config, mock_main_backup_path = security_engine_setup
        secret_path = mock_main_backup_path.parent / ".backy-secrets"
        secret_path.mkdir(exist_ok=True)
        # Create a dummy public key file to trigger loading, but make it invalid
        (secret_path / "public_key_v1.pem").touch()
        # Ensure _check_keys_exist returns True to trigger loading
        monkeypatch.setattr(SecurityEngine, "_check_keys_exist", lambda self: True)
        mocker.patch(
            "security.security_engine.open",
            side_effect=Exception("Mock load key error"),
        )
        # Attempt to initialize the SecurityEngine should raise an error
        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError) as excinfo:
                SecurityEngine(config)
            assert "Failed to load public key" in str(excinfo.value)
            assert "Error loading public key: Mock load key error" in caplog.text
