# security/engine/security_engine.py
import os
from pathlib import Path
from security.engine.key_generator import KeyGenerator
from security.engine.key_utils import KeyUtils
from security.key_store.key_store_manager import KeyStoreManager
from security.kms.kms_manager import KMSManager
from logger.logger_manager import LoggerManager
from typing import Tuple


class SecurityEngine:
    """
    SecurityEngine is responsible for orchestrating key management operations.
    It handles the generation, encryption, and decryption of keys based on the provided configuration.
    It supports different key management types such as keystore and KMS (Key Management Service).
    It uses KeyGenerator for generating keys and KeyUtils for key encryption and decryption.
    """

    def __init__(self, key_management_config: dict):
        """
        Initialize the SecurityEngine with the provided configuration.
        Args:
            key_management_config (dict): Configuration settings for key management.
        """
        self.logger = LoggerManager.setup_logger("security")
        self.type = key_management_config.get("type", "keystore")
        self.provider = key_management_config.get("provider", "local")
        self.key_size = key_management_config.get("key_size", 4096)
        self.key_version = key_management_config.get("key_version", None)
        self.encryption_file = key_management_config.get("encryption_file", '')
        self.key_generator = KeyGenerator()
        self.key_utils = KeyUtils()
        self.manager = None
        self.prcossiong_path = Path(os.getenv("MAIN_BACKUP_PATH"))

    def _assign_manager(self):
        """
        Assign the appropriate key management manager based on the type of key management system.
        This method initializes the KeyStoreManager or KMSManager based on the type and provider specified.
        Raises:
            ValueError: If the key management type is unsupported.
        """
        if self.type == "keystore":
            self.manager = KeyStoreManager(store_type=self.provider)
        elif self.type == "kms":
            self.manager = KMSManager(kms_provider=self.provider)
        else:
            self.logger.error(f"Unsupported key management type: {self.type}")
            raise ValueError(f"Unsupported key management type: {self.type}")

    def _generate_key_id_and_check_it(self) -> Tuple[bool, str, str]:
        """
        Generate a unique key identifier for the key based on the key version.
        If the key version is provided, it checks if the key already exists.
        If the key does not exist, it defaults to "auto" and checks if that key exists.
        If neither exists, it returns a default key identifier.
        Returns:
            Tuple[bool, str, str]: A tuple containing a boolean indicating if the key exists,
            the key identifier, and the key ID.
        """
        if self.key_version:
            key_id = f"backy_secret_key_{self.key_version}"
            if self.manager.validate_key(key_id):
                return True, key_id, key_id

        key_id = "auto"
        key_identifier = self.manager.validate_key(key_id)
        if key_identifier:
            return True, key_id, key_identifier

        key_id = "backy_secret_key_1"
        return False, key_id, key_id

    def _generate_private_keys(self, key_id: str) -> None:
        """
        Generate the private keys based on the type of key management system.
        If using a keystore, it generates an RSA private key and saves it.
        If using a KMS, it generates a key using the key management service.
        Args:
            key_id (str): Unique identifier for the key.
        """
        if self.type == "keystore":
            private_key = self.key_generator.generate_rsa_private_key(
                key_size=self.key_size
            )
            self.manager.save_key(key_id, private_key)
        else:
            self.manager.generate_key(key_id)

    def _get_public_key(self, key_id: str) -> bytes:
        """
        Retrieve the public key associated with the given key_id of the private key.
        This method extracts the public key from the private key if using a keystore,
        or retrieves it directly from the key management service.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            bytes: The public key associated with the given key_id.
        """
        if self.type == "keystore":
            private_key = self.manager.load_key(key_id)
            public_key = self.key_generator.extract_public_key(private_key=private_key)
            return public_key
        else:
            return self.manager.get_public_key(key_id)

    def _decrypt_symmetric_key(self, key_id: str, encrypted_key: bytes) -> bytes:
        """
        Decrypt the encrypted symmetric key using the private key.
        If using a keystore, it loads the private key and decrypts the symmetric key.
        If using a KMS, it retrieves the private key from the key management service.
        Args:
            key_id (str): Unique identifier for the key.
            encrypted_key (bytes): The encrypted symmetric key to be decrypted.
        Returns:
            bytes: The decrypted symmetric key.
        """
        if self.type == "keystore":
            private_key = self.manager.load_key(key_id)
            return self.key_utils.decrypt_symmetric_key_with_private_key(
                private_key, encrypted_key
            )
        else:
            return self.manager.decrypt_symmetric_key(key_id, encrypted_key)

    def _handle_new_symmetric_key(self, public_key):
        """
        Helper method to handle the generation of a new symmetric key and its encryption.
        This method generates a symmetric key, encrypts it using the provided public key,
        and returns both the symmetric key and its encrypted form.
        Args:
            public_key (bytes): The public key to encrypt the symmetric key.
        Returns:
            Tuple[bytes, bytes]: The symmetric key and its encrypted form.
        """
        symmetric_key = self.key_generator.generate_symmetric_key()
        encrypted = self.key_utils.encrypt_symmetric_key_with_public_key(
            symmetric_key, public_key
        )
        return symmetric_key, encrypted

    def _handle_existing_symmetric_key(self, key_id):
        """
        Helper method to handle the retrieval of an existing symmetric key.
        This method reads the encryption file, decrypts the symmetric key using the private key,
        and returns both the decrypted symmetric key and the encrypted symmetric key.
        Args:
            key_id (str): Unique identifier for the key.
        Returns:
            Tuple[bytes, bytes]: The decrypted symmetric key and the encrypted symmetric key.
        """
        encrypted = self.key_utils.read_encryption_file(self.prcossiong_path / self.encryption_file)
        symmetric = self._decrypt_symmetric_key(key_id, encrypted)
        return symmetric, encrypted

    def get_keys(self) -> Tuple[bytes, bytes, str]:
        """
        The entry point for retrieving keys which orchestrates the key management operations.
        It provide the only interface to retrieve the key_id, symmetric key, and encrypted symmetric key.
        It handles both the generation of new keys and the retrieval of existing keys.
        Returns:
            bytes: The symmetric key in both encrypted and decrypted form and key_id.
            str: The unique key identifier.
        Raises:
            RuntimeError: If there is an error during the key generation or retrieval.
        Returns:
            Tuple[bytes, bytes, str]: The symmetric key, encrypted symmetric key, and key_id.
        """
        try:
            # step 1: Assign the appropriate key management manager
            self._assign_manager()
            # step 2: Generate a unique key identifier with a check for its existence
            existing, key_id, key_identifier = self._generate_key_id_and_check_it()

            # step 3: Check if the keys not exist
            if not existing:
                # step 4: Generate the private keys if they do not exist
                self._generate_private_keys(key_id)
            # step 5: Retrieve the public key associated with the key_id
            public_key = self._get_public_key(key_id)
            # step 6: if there is no encryption file, generate a symmetric key and encrypt it
            if not self.encryption_file:
                symmetric, encrypted = self._handle_new_symmetric_key(public_key)
                return symmetric, encrypted, key_identifier
            # step 7: if there is an encryption file, read it and decrypt the symmetric
            symmetric, encrypted = self._handle_existing_symmetric_key(key_id)
            return symmetric, encrypted, key_identifier
        except Exception as e:
            self.logger.error(f"Error retrieving keys: {e}")
            raise RuntimeError("Error retrieving keys") from e
