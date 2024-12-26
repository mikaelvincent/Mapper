import os
import subprocess
import sys

def test_map_init_creates_files(tmp_path):
    """
    Verify that 'map init' creates the required Mapper files
    if they do not exist.
    """
    # Move into a temporary directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "init"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0

        # Check that each file now exists
        required_files = [
            ".mapheader",
            ".mapfooter",
            ".mapignore",
            ".mapomit",
            ".mapinclude",
            ".mapconfig"
        ]
        for f in required_files:
            assert os.path.exists(f), f"Expected {f} to be created."

    finally:
        os.chdir(original_dir)

def test_map_init_skips_existing_files(tmp_path):
    """
    Confirm that 'map init' does not overwrite existing files.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    # Pre-create one of the files
    existing_file = ".mapignore"
    with open(existing_file, "w", encoding="utf-8") as f:
        f.write("Pre-existing content")

    try:
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "init"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0

        # File content should remain unchanged
        with open(existing_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "Pre-existing content"

    finally:
        os.chdir(original_dir)
