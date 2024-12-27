import os
import subprocess
import sys
import pytest

@pytest.mark.usefixtures("in_temp_dir")
def test_map_init_creates_files():
    """
    Verify that 'map init' creates the required Mapper files
    if they do not exist.
    """
    process = subprocess.run(
        [sys.executable, "-m", "mapper", "init"],
        capture_output=True,
        text=True
    )
    assert process.returncode == 0

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

@pytest.mark.usefixtures("in_temp_dir")
def test_map_init_skips_existing_files():
    """
    Confirm that 'map init' does not overwrite existing files.
    """
    existing_file = ".mapignore"
    with open(existing_file, "w", encoding="utf-8") as f:
        f.write("Pre-existing content")

    process = subprocess.run(
        [sys.executable, "-m", "mapper", "init"],
        capture_output=True,
        text=True
    )
    assert process.returncode == 0

    with open(existing_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "Pre-existing content"
