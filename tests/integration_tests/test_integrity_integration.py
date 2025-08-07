# tests/ integration_tests/test_integrity_integration.py
import pytest
from integrity.integrity_manager import IntegrityManager
from pathlib import Path
import os


@pytest.mark.parametrize("integrity_type", ["hmac", "checksum"])
class TestIntegrityIntegration:
    """ """

    @pytest.fixture(autouse=True)
    def setup(self, integrity_type, monkeypatch):
        """
        Setup method to initialize IntegrityManager with the specified integrity type
        """
        monkeypatch.setenv("INTEGRITY_PASSWORD", "test_password")

        process_path = Path(os.getenv("MAIN_BACKUP_PATH"))
        first_file = process_path / "test_file.txt"
        first_file.write_text("This is a test file for integrity checks.")
        second_file = process_path / "test_file_2.txt"
        second_file.write_text("This is another test file for integrity checks.")

        self.files = [first_file, second_file]
        self.integrity_manager = IntegrityManager(integrity_type)

    def test_create_integrity_then_check_if_valid(self):
        """
        Test creating an integrity file and verifying its validity
        """
        integrity_file = self.integrity_manager.create_integrity()
        assert integrity_file.is_file()
        with open(integrity_file, "r") as f:
            content = f.read()
            assert self.files[0].name in content
            assert self.files[1].name in content

        is_valid = self.integrity_manager.verify_integrity(integrity_file)
        assert is_valid is True

    def test_verify_integrity_with_tempered_file(self):
        """
        Test verifying integrity with a tempered file
        """
        integrity_file = self.integrity_manager.create_integrity()
        assert integrity_file.is_file()

        # Temper the first file
        self.files[0].write_text("This file has been tempered.")

        is_valid = self.integrity_manager.verify_integrity(integrity_file)
        assert is_valid is False

    def test_verify_integrity_with_tempered_integrity_file(self):
        """
        Test verifying integrity with a tempered integrity file
        """
        integrity_file = self.integrity_manager.create_integrity()
        assert integrity_file.is_file()

        # Temper the integrity file
        with open(integrity_file, "a") as f:
            f.write("tempered_checksum  tempered_file.txt\n")

        is_valid = self.integrity_manager.verify_integrity(integrity_file)
        assert is_valid is False

    def test_verify_integrity_with_different_password(self, integrity_type):
        """
        Test verifying integrity with a different password
        """
        if integrity_type != "hmac":
            pytest.skip("⚠️ Skipping test: Only applicable for HMAC integrity type.")
        integrity_file = self.integrity_manager.create_integrity()
        assert integrity_file.is_file()

        # Change the environment variable to a different password
        os.environ["INTEGRITY_PASSWORD"] = "different_password"
        new_integrity_manager = IntegrityManager(integrity_type)

        is_valid = new_integrity_manager.verify_integrity(integrity_file)
        assert is_valid is False
