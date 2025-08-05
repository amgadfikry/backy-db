# tests/security/engine/test_key_utils.py
import os
from security.engine.key_utils import KeyUtils
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding


class TestKeyUtils:
    """
    Test suite for the KeyUtils class.
    This class contains tests for encrypting symmetric keys with public keys.
    """

    @pytest.fixture
    def key_utils(self, monkeypatch):
        """
        Fixture to create an instance of KeyUtils.
        """
        # Set the environment variable for the private key password
        monkeypatch.setenv("PRIVATE_KEY_PASSWORD", "test_password")
        # Generate private key for testing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        # Save the private key and encrypt with a password
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                os.environ.get("PRIVATE_KEY_PASSWORD", "").strip().encode()
            ),
        )
        # extract the public key from the private key
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # Generate a symmetric key for testing
        symmetric_key = AESGCM.generate_key(bit_length=128)
        # Return the keys
        return symmetric_key, public_key_bytes, private_key_bytes

    def test_encrypt_symmetric_key_with_public_key_success(self, key_utils):
        """
        Test the encryption of a symmetric key using a public key successfully.
        """
        symmetric_key, public_key_bytes, _ = key_utils
        key_utils_instance = KeyUtils()
        encrypted_symmetric_key = (
            key_utils_instance.encrypt_symmetric_key_with_public_key(
                symmetric_key=symmetric_key, public_key=public_key_bytes
            )
        )
        assert encrypted_symmetric_key is not None
        assert len(encrypted_symmetric_key) > 0

    def test_encrypt_symmetric_key_with_public_key_failure(self, key_utils, mocker):
        """
        Test the failure of symmetric key encryption with a public key.
        """
        symmetric_key, public_key_bytes, _ = key_utils
        key_utils_instance = KeyUtils()
        # Mock the serialization.load_pem_public_key method to raise an exception
        mocker.patch(
            "cryptography.hazmat.primitives.serialization.load_pem_public_key",
            side_effect=Exception("Mocked exception"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            key_utils_instance.encrypt_symmetric_key_with_public_key(
                symmetric_key=symmetric_key, public_key=public_key_bytes
            )
        assert "Failed to encrypt the symmetric key" in str(exc_info.value)

    def test_decrypt_symmetric_key_with_private_key_success(self, key_utils):
        """
        Test the decryption of a symmetric key using a private key successfully.
        """
        symmetric_key, public_key_bytes, private_key_bytes = key_utils
        key_utils_instance = KeyUtils()
        # Encrypt the symmetric key first
        public_key_obj = serialization.load_pem_public_key(public_key_bytes)
        encrypted_symmetric_key = public_key_obj.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        # Now decrypt the symmetric key
        decrypted_symmetric_key = (
            key_utils_instance.decrypt_symmetric_key_with_private_key(
                private_key=private_key_bytes, symmetric_key=encrypted_symmetric_key
            )
        )
        assert decrypted_symmetric_key == symmetric_key
        assert len(decrypted_symmetric_key) == len(symmetric_key)

    def test_decrypt_symmetric_key_with_private_key_failure(self, key_utils, mocker):
        """
        Test the failure of symmetric key decryption with a private key.
        """
        symmetric_key, public_key_bytes, private_key_bytes = key_utils
        key_utils_instance = KeyUtils()
        # Encrypt the symmetric key first
        public_key_obj = serialization.load_pem_public_key(public_key_bytes)
        encrypted_symmetric_key = public_key_obj.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        # Mock the serialization.load_pem_private_key method to raise an exception
        mocker.patch(
            "cryptography.hazmat.primitives.serialization.load_pem_private_key",
            side_effect=Exception("Mocked exception"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            key_utils_instance.decrypt_symmetric_key_with_private_key(
                private_key=private_key_bytes, symmetric_key=encrypted_symmetric_key
            )
        assert "Failed to decrypt the symmetric key" in str(exc_info.value)

    def test_read_encryption_file_success(self, key_utils, tmp_path):
        """
        Test reading an encryption file successfully.
        """
        symmetric_key, public_key_bytes, _ = key_utils
        key_utils_instance = KeyUtils()
        # Generate encrypted symmetric key
        public_key_obj = serialization.load_pem_public_key(public_key_bytes)
        encrypted_symmetric_key = public_key_obj.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        # Write the encrypted symmetric key to a file
        encryption_file = tmp_path / "encryption_file.pem"
        with open(encryption_file, "wb") as f:
            f.write(encrypted_symmetric_key)
        # Read the encryption file
        read_symmetric_key = key_utils_instance.read_encryption_file(encryption_file)
        assert read_symmetric_key == encrypted_symmetric_key

    def test_read_encryption_file_no_file(self, tmp_path):
        """
        Test reading an encryption file that does not exist.
        """
        key_utils_instance = KeyUtils()
        encryption_file = tmp_path / "non_existent_file.pem"
        with pytest.raises(FileNotFoundError) as exc_info:
            key_utils_instance.read_encryption_file(encryption_file)
        assert f"Encryption file {encryption_file} does not exist." in str(
            exc_info.value
        )

    def test_read_encryption_file_failure(self, tmp_path, mocker):
        """
        Test the failure of reading an encryption file.
        This test mocks the open function to raise an exception.
        """
        key_utils_instance = KeyUtils()
        mocker.patch("builtins.open", side_effect=Exception("Mocked exception"))
        encryption_file = tmp_path / "encryption_file.pem"
        encryption_file.touch()
        with pytest.raises(RuntimeError) as exc_info:
            key_utils_instance.read_encryption_file(encryption_file)
        assert "Failed to read encryption file" in str(exc_info.value)
