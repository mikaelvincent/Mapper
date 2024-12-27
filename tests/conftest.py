import os
import pytest

@pytest.fixture
def in_temp_dir(tmp_path):
    """
    Change to a temporary directory and revert to the original directory
    upon test completion.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original_dir)
