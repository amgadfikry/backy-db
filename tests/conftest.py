# tests/conftest.py
import os
import pytest
from pathlib import Path
import shutil

@pytest.fixture(scope="session", autouse=True)
def configure_logging_path():
    """
    Sets up a test-only logging directory and LOGGING_PATH env var.
    Cleans it up after the test session.
    """
    test_log_path = Path.cwd() / "logs" / "backydb"
    os.environ["LOGGING_PATH"] = str(test_log_path)
    test_log_path.mkdir(parents=True, exist_ok=True)

    yield

    # Teardown: only delete if we know it's the test path
    if test_log_path.parent.exists() and test_log_path.parent.is_dir():
        shutil.rmtree(test_log_path.parent, ignore_errors=True)
    os.environ.pop("LOGGING_PATH", None)
