# tests/integrity/test_integrity_manager.py
from integrity.integrity_manager import IntegrityManager
import pytest


class TestIntegrityManager:
    """
    Test class for IntegrityManager functionality
    """

    @pytest.fixture(autouse=True)
    def setup(self, mocker, monkeypatch):
        """
        Setup method to initialize IntegrityManager before each test
        """
        self.hmac_mocker = mocker.Mock()
        self.hmac_mocker.create_integrity.return_value = mocker.Mock()
        self.hmac_mocker.verify_integrity.return_value = mocker.Mock()
        monkeypatch.setitem(
            IntegrityManager.INTEGRITY_TYPES, "hmac", lambda: self.hmac_mocker
        )
        self.integrity_manager = IntegrityManager("hmac")

    def test_create_integrity(self, mocker):
        """
        Test the create_integrity method of IntegrityManager
        """
        integrity_file = self.integrity_manager.create_integrity()
        assert integrity_file is not None
        assert self.hmac_mocker.create_integrity.called

    def test_verify_integrity(self, mocker):
        """
        Test the verify_integrity method of IntegrityManager
        """
        integrity_file = mocker.Mock()
        result = self.integrity_manager.verify_integrity(integrity_file)
        assert result is not None
        assert self.hmac_mocker.verify_integrity.called
        assert self.hmac_mocker.verify_integrity.call_args[0][0] == integrity_file

    def test_invalid_integrity_type(self):
        """
        Test that IntegrityManager raises ValueError for unsupported integrity types
        """
        with pytest.raises(ValueError) as exc_info:
            IntegrityManager("invalid_type")
        assert "Unsupported integrity type: invalid_type" in str(exc_info.value)
