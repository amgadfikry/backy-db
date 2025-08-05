# tests/conftest.py
import os
import pytest
from pathlib import Path
import socket
from dotenv import load_dotenv

load_dotenv()


def is_mysql_running():
    """
    Check if MySQL is running by attempting to connect to the default port.
    Returns:
        bool: True if MySQL is running, False otherwise.
    """
    try:
        with socket.create_connection(("localhost", 3306), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

@pytest.fixture
def require_mysql():
    """
    Fixture to skip tests if MySQL is not running.
    This fixture checks if MySQL is running and skips the test if it is not.
    """
    if not is_mysql_running():
        pytest.skip("⚠️ Skipping test: MySQL is not running.")

@pytest.fixture
def require_aws_credentials():
    """
    Fixture to skip tests if AWS credentials are not set.
    This fixture checks for the presence of AWS environment variables
    and skips the test if they are not set.
    """
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not aws_key or not aws_secret:
        pytest.skip("⚠️ Skipping test: Missing AWS credentials.")

@pytest.fixture
def require_gcp_credentials():
    """
    Fixture to skip tests if GCP credentials are not set.
    This fixture checks for the presence of the GCP credentials file environment variable
    and skips the test if it is not set or the file does not exist.
    """
    gcp_cred_var = "GOOGLE_APPLICATION_CREDENTIALS"
    if not os.getenv(gcp_cred_var) or not Path(os.getenv(gcp_cred_var)).exists():
        pytest.skip("⚠️ Skipping test: Missing or invalid GCP credentials file.")

@pytest.fixture(autouse=True)
def configure_logging_path(tmp_path, monkeypatch):
    """
    Fixture to set up the logging path and main backup path for tests.
    This fixture creates temporary directories for logging and backups,
    and sets the corresponding environment variables.
    """
    # change home directory to tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Create logging and backup directories and set environment variables
    logging_path = tmp_path / "logs"
    logging_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LOGGING_PATH", str(logging_path))
    # Create the main backup directory and set the environment variable
    process_path = tmp_path / "backups"
    process_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MAIN_BACKUP_PATH", str(process_path))
    yield
