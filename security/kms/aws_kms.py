# security/kms/aws_kms.py
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import boto3
from security.kms.kms_base import KMSBase
import os
from cryptography.hazmat.primitives import serialization

load_dotenv()


class AWSKMS(KMSBase):
    """
    AWS KMS implementation for managing cryptographic keys.
    This class provides methods to generate asymmetric keys, retrieve public keys,
    and decrypt symmetric keys using AWS KMS.
    It extends the KMSBase class, which defines the interface for key management operations.
    """

    def __init__(self):
        """
        Initialize the AWS KMS client with the specified region.
        """
        super().__init__()
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.kms_client = boto3.client("kms", region_name=self.region)

    def generate_key(self, alias_name: str) -> str:
        """
        This method creates a new KMS key and associates it with an alias.
        Args:
            alias_name (str): Name for the key alias.
        Returns:
            str: alias name for the generated key.
        Raises:
            RuntimeError: If the key creation fails.
        """
        try:
            response = self.kms_client.create_key(
                Description="Asymmetric key for BackyDB hybrid encryption",
                KeyUsage="ENCRYPT_DECRYPT",
                CustomerMasterKeySpec="RSA_4096",
                Origin="AWS_KMS",
            )
            key_id = response["KeyMetadata"]["KeyId"]
            self.logger.info(f"AWS KMS key created: {key_id}")
            return self._create_alias(key_id, alias_name)
        except ClientError as e:
            self.logger.error(f"Failed to create KMS key: {e}")
            raise RuntimeError(f"Failed to create KMS key: {e}")

    def get_public_key(self, key_id: str) -> bytes:
        """
        This method fetches the public key associated with the given key_id.
        It returns the public key in PEM format, which can be used for encryption.
        Args:
            key_id (str): AWS KMS KeyId or ARN
        Returns:
            bytes: PEM-encoded public key
        Raises:
            RuntimeError: If the public key retrieval fails.
        """
        try:
            the_key_id = self._get_key(key_id)
            response = self.kms_client.get_public_key(KeyId=the_key_id)
            der_bytes = response["PublicKey"]
            self.logger.info(f"Retrieved public key for {key_id}")
            return self._convert_der_key_to_pem(der_bytes)
        except ClientError as e:
            self.logger.error(f"Failed to retrieve public key for {key_id}: {e}")
            raise RuntimeError(f"Failed to retrieve public key: {e}")

    def decrypt_symmetric_key(self, key_id: str, encrypted_key: bytes) -> bytes:
        """
        This method uses the AWS KMS client to decrypt the provided encrypted_key.
        It requires the key_id to be a valid KMS KeyId
        Args:
            key_id (str): AWS KMS KeyId or ARN
            encrypted_key (bytes): Encrypted symmetric key
        Returns:
            bytes: Decrypted symmetric key
        Raises:
            ValueError: If the encrypted_key is empty.
            RuntimeError: If the decryption fails.
        """
        if not encrypted_key:
            self.logger.error("Encrypted key is empty.")
            raise ValueError("Encrypted key is empty.")

        try:
            the_key_id = self._get_key(key_id)
            response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_key,
                KeyId=the_key_id,
                EncryptionAlgorithm="RSAES_OAEP_SHA_256",
            )
            decrypted_key = response["Plaintext"]
            self.logger.info(f"Symmetric key decrypted successfully with {key_id}")
            return decrypted_key
        except ClientError as e:
            self.logger.error(f"Failed to decrypt symmetric key: {e}")
            raise RuntimeError(f"Failed to decrypt symmetric key: {e}")

    def validate_key(self, key_id: str) -> str | None:
        """
        This method checks if the key exists and is enabled.
        It resolves the alias to the actual KeyId if necessary.
        It get the metadata of the key and checks its state.
        Args:
            key_id (str): AWS KMS KeyId or alias (e.g., 'alias/my_key')
        Raises:
            ValueError: If the key_id is invalid.
            RuntimeError: If the key does not exist or is not enabled.
        Returns:
            bool: True if the key exists and is enabled, False otherwise.
        """
        try:
            the_key_id = self._get_key(key_id)
            if not the_key_id:
                self.logger.error(f"No key found for alias {key_id}.")
                return None

            response = self.kms_client.describe_key(KeyId=the_key_id)
            key_state = response["KeyMetadata"]["KeyState"]

            if key_state == "Enabled":
                self.logger.info(f"KMS key {key_id} is valid and enabled.")
                return the_key_id.split("/")[-1]
            else:
                self.logger.error(f"KMS key {key_id} exists but is not enabled.")
                return None

        except ClientError as e:
            self.logger.error(f"Failed to validate KMS key {key_id}: {e}")
            return None

    def delete_key(self, key_id: str) -> None:
        """
        This method schedules the deletion of the KMS key.
        The key will be deleted after a waiting period of 7 days.
        Args:
            key_id (str): AWS KMS KeyId or alias (e.g., 'alias/my_key')
        Raises:
            RuntimeError: If the key deletion fails.
        """
        try:
            the_key_id = self._get_key(key_id)
            key_without_alias = self._resolve_alias_to_key_id(the_key_id)
            self.kms_client.schedule_key_deletion(
                KeyId=key_without_alias, PendingWindowInDays=7
            )
            self.logger.info(f"KMS key {key_id} scheduled for deletion.")
        except ClientError as e:
            self.logger.error(f"Failed to delete KMS key {key_id}: {e}")
            raise RuntimeError(f"Failed to delete KMS key: {e}")

    def _create_alias(self, key_id: str, alias_name: str) -> str:
        """
        This method creates an alias for the KMS key, which can be used to refer to
        the key in a more human-readable way.
        Args:
            key_id (str): Unique identifier for the key.
            alias_name (str): Name for the alias.
        Returns:
            str: The alias name created.
        """
        try:
            self.kms_client.create_alias(
                AliasName=f"alias/{alias_name}", TargetKeyId=key_id
            )
            self.logger.info(f"Alias alias/{alias_name} created for key {key_id}")
            return alias_name
        except ClientError as e:
            self.logger.error(f"Failed to create alias: {e}")
            raise RuntimeError(f"Failed to create alias: {e}")

    def _get_key(self, key_id: str) -> str | None:
        """
        Get the KMS key associated with the given key_id.
        If key_id is "auto", it resolves to the latest alias.
        If key_id is an alias, it resolves to the actual KeyId.
        Args:
            key_id (str): The key ID or alias to resolve.
        Returns:
            str: The latest alias name (e.g., 'alias/backy_2024_08_03')
        Raises:
            RuntimeError: If no matching aliases found.
        """
        try:
            if key_id == "auto":
                aliases = self.kms_client.list_aliases()["Aliases"]
                custom_aliases = [
                    a
                    for a in aliases
                    if a["AliasName"].startswith("alias/backy_") and "TargetKeyId" in a
                ]
                if not custom_aliases:
                    return None
                # Sort descending (assuming names have sortable suffixes like key_YYYY_MM_DD)
                latest = sorted(
                    custom_aliases, key=lambda a: a["AliasName"], reverse=True
                )[0]
                return latest["AliasName"]
            else:
                return f"alias/{key_id}"
        except ClientError as e:
            self.logger.error(f"Failed to resolve latest key: {e}")
            raise RuntimeError(f"Failed to resolve latest key: {e}") from e

    def _convert_der_key_to_pem(self, der_key: bytes) -> bytes:
        """
        This method uses the cryptography library to convert the DER-encoded public key
        to PEM format.
        Args:
            der_key (bytes): The DER-encoded key.
        Returns:
            bytes: The PEM-encoded key.
        Raises:
            RuntimeError: If the conversion fails.
        """
        try:
            public_key_obj = serialization.load_der_public_key(der_key)
            pem = public_key_obj.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return pem
        except Exception as e:
            self.logger.error(f"Failed to convert DER key to PEM: {e}")
            raise RuntimeError(f"Failed to convert DER key to PEM: {e}") from e

    def _resolve_alias_to_key_id(self, alias_name: str) -> str:
        """
        Resolve an alias to its actual KeyId.
        This method checks if the alias exists and returns the KeyId associated with it.
        Args:
            alias_name (str): The alias name to resolve.
        Returns:
            str: The KeyId associated with the alias.
        Raises:
            RuntimeError: If the alias does not exist or cannot be resolved.
        """
        try:
            if not alias_name.startswith("alias/"):
                alias_name = f"alias/{alias_name}"
            response = self.kms_client.describe_key(KeyId=alias_name)
            return response["KeyMetadata"]["KeyId"]
        except ClientError as e:
            self.logger.error(f"Failed to resolve alias to key ID: {e}")
            raise RuntimeError("Failed to resolve alias to key ID") from e
