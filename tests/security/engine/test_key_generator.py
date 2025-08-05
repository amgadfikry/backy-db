# tests/security/engine/test_key_generator.py
import os
from security.engine.key_generator import KeyGenerator
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class TestKeyGenerator:
    """
    Test suite for the KeyGenerator class.
    This class contains tests for generating symmetric, RSA keys, and extracting public keys from private keys.
    """

    def test_generate_symmetric_key_success(self):
        """
        This test checks if a symmetric key is generated successfully with the default bit length.
        """
        key_gen = KeyGenerator()
        key = key_gen.generate_symmetric_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_generate_symmetric_key_with_specific_length(self):
        """
        This test checks if a symmetric key of the specified length is generated successfully.
        """
        key_gen = KeyGenerator()
        key = key_gen.generate_symmetric_key(bit_length=128)
        assert isinstance(key, bytes)
        assert len(key) == 16

    def test_generate_symmetric_key_failure(self, mocker):
        """
        This test when the symmetric key generation fails.
        """
        key_gen = KeyGenerator()
        # Mock the AESGCM.generate_key method to raise an exception
        mocker.patch(
            "cryptography.hazmat.primitives.ciphers.aead.AESGCM.generate_key",
            side_effect=Exception("Mocked exception"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            key_gen.generate_symmetric_key()
        assert "Failed to generate symmetric key" in str(exc_info.value)

    def test_generate_rsa_private_key_success(self):
        """
        Test the generation of an RSA private key successfully with the default key size.
        """
        key_gen = KeyGenerator()
        private_key = key_gen.generate_rsa_private_key()
        assert isinstance(private_key, bytes)
        assert b"-----BEGIN RSA PRIVATE KEY-----" in private_key
        assert b"-----END RSA PRIVATE KEY-----" in private_key

    def test_generate_rsa_private_key_with_specific_size(self):
        """
        Test the generation of an RSA private key with a specific key size.
        """
        key_gen = KeyGenerator()
        private_key = key_gen.generate_rsa_private_key(key_size=2048)
        assert isinstance(private_key, bytes)
        assert b"-----BEGIN RSA PRIVATE KEY-----" in private_key
        assert b"-----END RSA PRIVATE KEY-----" in private_key

    def test_generate_rsa_private_key_failure(self, mocker):
        """
        Test the failure of RSA private key generation.
        """
        key_gen = KeyGenerator()
        # Mock the rsa.generate_private_key method to raise an exception
        mocker.patch(
            "cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key",
            side_effect=Exception("Mocked exception"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            key_gen.generate_rsa_private_key()
        assert "Failed to generate RSA private key" in str(exc_info.value)

    def test_extract_public_key_from_private_key_encrypted_with_password_success(
        self, monkeypatch
    ):
        """
        Test the extraction of a public key from a private key encrypted with a password successfully.
        """
        # Set the environment variable for the private key password
        monkeypatch.setenv("PRIVATE_KEY_PASSWORD", "testpassword")
        key_gen = KeyGenerator()
        # Generate a private key and encrypt it with the password
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                os.getenv("PRIVATE_KEY_PASSWORD").strip().encode()
            ),
        )
        # Extract the public key from the private key
        public_key = key_gen.extract_public_key(private_key_bytes)
        assert isinstance(public_key, bytes)
        assert b"-----BEGIN PUBLIC KEY-----" in public_key
        assert b"-----END PUBLIC KEY-----" in public_key

    def test_extract_public_key_from_private_key_if_not_found(self):
        """
        Test the extraction of a public key from a private key when the private key is not provided.
        """
        key_gen = KeyGenerator()
        with pytest.raises(ValueError) as exc_info:
            key_gen.extract_public_key(b"")
        assert "Private key must be provided to extract the public key." in str(
            exc_info.value
        )

    def test_extract_public_key_from_private_key_failure(self, mocker):
        """
        Test the failure of extracting a public key from a private key.
        """
        key_gen = KeyGenerator()
        mocker.patch(
            "cryptography.hazmat.primitives.serialization.load_pem_private_key",
            side_effect=Exception("Mocked exception"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            key_gen.extract_public_key(b"invalid private key")
        assert "Error extracting public key" in str(exc_info.value)
