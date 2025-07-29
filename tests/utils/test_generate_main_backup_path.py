# tests/utils/test_generate_main_backup_path.py
import pytest
from utils.generate_main_backup_path import generate_main_backup_path
from pathlib import Path
import os
import platform

@pytest.fixture
def setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("MAIN_BACKUP_PATH", raising=False)
    return tmp_path


class TestGenerateMainBackupPath:
    """
    Test cases for the generate_main_backup_path function.
    """
    @pytest.mark.parametrize(
        "system_name,expected_parts",
        [
            ("Linux", [".local", "share"]),
            ("Darwin", ["Library", "Application Support"]),
            ("Windows", ["AppData", "Roaming"]),
        ]
    )
    def test_os_generate_main_backup_path_default(self, monkeypatch, setup_env, system_name, expected_parts):
        monkeypatch.setattr(platform, "system", lambda: system_name)
        backup_path = generate_main_backup_path()
        assert backup_path.is_dir()
        assert os.environ["MAIN_BACKUP_PATH"] == str(backup_path)
        for part in expected_parts:
            assert part in str(backup_path)

    @pytest.mark.parametrize(
        "system_name,subfolder,expected_parts",
        [
            ("Linux", "test_subfolder", [".local", "share", "test_subfolder"]),
            ("Darwin", "test_subfolder", ["Library", "Application Support", "test_subfolder"]),
            ("Windows", "test_subfolder", ["AppData", "Roaming", "test_subfolder"]),
        ]
    )
    def test_os_generate_main_backup_path_with_subfolder(self, monkeypatch, setup_env, system_name, subfolder, expected_parts):
        monkeypatch.setattr(platform, "system", lambda: system_name)
        backup_path = generate_main_backup_path(subfolder)
        assert backup_path.is_dir()
        assert os.environ["MAIN_BACKUP_PATH"] == str(backup_path)
        for part in expected_parts:
            assert part in str(backup_path)
