# tests/config_schemas.py/schemas/test_security_schema.py
from config_schemas.schemas.security_schema import SecuritySchema
import pytest


class TestSecuritySchema:
    """
    Test cases for SecuritySchema.
    This class contains tests to validate the SecuritySchema
    and ensure it behaves as expected.
    """

    def test_security_schema_with_default_values(self):
        """
        Test SecuritySchema with default values.
        """
        schema = SecuritySchema()
        assert schema.encryption is False
        assert schema.type is None
        assert schema.provider is None
        assert schema.key_size is None
        assert schema.key_version is None

    def test_security_schema_with_custom_values(self):
        """
        Test SecuritySchema with custom values.
        """
        schema = SecuritySchema(
            encryption=True, type="kms", provider="aws", key_size=2048, key_version="v1"
        )
        assert schema.encryption is True
        assert schema.type == "kms"
        assert schema.provider == "aws"
        assert schema.key_size == 2048
        assert schema.key_version == "v1"

    def test_security_schema_with_encryption_without_type_and_provider(self):
        """
        Test SecuritySchema with encryption enabled but without type and provider.
        """
        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(encryption=True)
        assert (
            "Both type and provider must be specified when encryption is enabled."
            in str(exc_info.value)
        )

    def test_security_schema_with_invalid_type_and_provider(self):
        """
        Test SecuritySchema with invalid type and provider combinations.
        """
        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(encryption=True, type="kms", provider="local")
        assert "KMS type requires AWS provider." in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(encryption=True, type="keystore", provider="aws")
        assert "Keystore type requires local or GCP provider." in str(exc_info.value)

    def test_security_schema_with_invalid_key_size(self):
        """
        Test SecuritySchema with an invalid key size.
        """
        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(
                encryption=True, type="keystore", provider="local", key_size=1024
            )
        assert "validation error" in str(exc_info.value)
        assert "key_size" in str(exc_info.value)

    def test_security_schema_with_invalid_type(self):
        """
        Test SecuritySchema with an invalid type.
        """
        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(encryption=True, type="invalid_type", provider="aws")
        assert "validation error" in str(exc_info.value)
        assert "type" in str(exc_info.value)

    def test_security_schema_with_invalid_provider(self):
        """
        Test SecuritySchema with an invalid provider.
        """
        with pytest.raises(ValueError) as exc_info:
            SecuritySchema(
                encryption=True, type="keystore", provider="invalid_provider"
            )
        assert "validation error" in str(exc_info.value)
        assert "provider" in str(exc_info.value)

    def test_security_schema_with_key_version(self):
        """
        Test SecuritySchema with a key version.
        """
        schema = SecuritySchema(
            encryption=True, type="keystore", provider="local", key_version="v2"
        )
        assert schema.key_version == "v2"
