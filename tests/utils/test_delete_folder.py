# tests/utils/test_delete_folder.py
import pytest
from utils.delete_folder import delete_folder


class TestDeleteFolder:
    """
    Test suite for the delete_folder function.
    """

    def test_delete_existing_folder(self, tmp_path):
        """
        Test that an existing folder and its contents are deleted.
        """
        folder = tmp_path / "folder_to_delete"
        folder.mkdir()
        (folder / "dummy.txt").write_text("hello")
        assert folder.exists()
        delete_folder(folder)
        assert not folder.exists()

    def test_delete_non_existing_folder(self, tmp_path, caplog):
        """
        Test that a non-existing folder does not raise an error but logs a warning.
        """
        non_existing = tmp_path / "nope"
        delete_folder(non_existing)
        assert (
            f"Folder {non_existing} does not exist or is not a directory."
            in caplog.text
        )

    def test_delete_file_instead_of_folder(self, tmp_path, caplog):
        """
        Test that trying to delete a file instead of a folder logs a warning and does not raise an error.
        """
        file_path = tmp_path / "some_file.txt"
        file_path.touch()
        assert file_path.exists()
        delete_folder(file_path)
        assert (
            f"Folder {file_path} does not exist or is not a directory." in caplog.text
        )
        assert file_path.exists()

    def test_permission_error_raises(self, tmp_path, mocker):
        """
        Test that a permission error during deletion raises a RuntimeError.
        """
        mocker.patch(
            "utils.delete_folder.shutil.rmtree",
            side_effect=PermissionError("Permission denied"),
        )
        folder = tmp_path / "protected_folder"
        folder.mkdir()
        with pytest.raises(RuntimeError):
            delete_folder(folder)
