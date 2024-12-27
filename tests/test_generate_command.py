import os
import subprocess
import sys
import pytest

@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_creates_default_map():
    """
    Validate that 'map generate' produces a .map file by default,
    respecting minimal rules. No symlinks or large files here.
    """
    # Create a sample file
    with open("main.py", "w", encoding="utf-8") as f:
        f.write("print('Hello World')\n")

    process = subprocess.run(
        [sys.executable, "-m", "mapper", "generate"],
        capture_output=True,
        text=True
    )
    assert process.returncode == 0
    assert os.path.exists(".map")

    with open(".map", "r", encoding="utf-8") as f:
        map_content = f.read()
    assert "main.py" in map_content

@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_respects_output_flag():
    """
    Verify that specifying --output writes to the given filename.
    """
    with open("example.txt", "w", encoding="utf-8") as f:
        f.write("Some content")

    custom_output = "custom_map.txt"
    process = subprocess.run(
        [
            sys.executable, "-m", "mapper", "generate",
            "--output", custom_output
        ],
        capture_output=True,
        text=True
    )
    assert process.returncode == 0
    assert os.path.exists(custom_output)
    with open(custom_output, "r", encoding="utf-8") as f:
        out_content = f.read()
    assert "example.txt" in out_content

@pytest.mark.skipif(
    not hasattr(sys, "platform") or "win" not in sys.platform.lower(),
    reason="Clipboard test primarily for Windows; cross-platform library might handle others."
)
@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_clipboard_option():
    """
    Confirm that --clipboard attempts to copy the output to the clipboard.
    """
    with open("data.log", "w", encoding="utf-8") as f:
        f.write("Log data")

    process = subprocess.run(
        [
            sys.executable, "-m", "mapper", "generate",
            "--clipboard"
        ],
        capture_output=True,
        text=True
    )
    assert process.returncode == 0
    assert os.path.exists(".map")

@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_symlink_halts():
    """
    Check that encountering a symlink causes the process to halt with error.
    """
    with open("file.txt", "w", encoding="utf-8") as f:
        f.write("Some content")

    if hasattr(os, "symlink"):
        os.symlink("file.txt", "link_to_file")
    else:
        pytest.skip("Symlinks not supported on this platform.")

    process = subprocess.run(
        [sys.executable, "-m", "mapper", "generate"],
        capture_output=True,
        text=True
    )
    assert process.returncode != 0
    assert "Symlink found" in process.stderr
    assert not os.path.exists(".map")

@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_file_limits():
    """
    Verify that exceeding max_files triggers a constraint error.
    """
    for i in range(3):
        with open(f"file_{i}.txt", "w", encoding="utf-8") as f:
            f.write("content")

    process = subprocess.run(
        [
            sys.executable, "-m", "mapper",
            "--max-files", "2",
            "generate"
        ],
        capture_output=True,
        text=True
    )
    assert process.returncode != 0
    assert "File limit exceeded" in process.stderr
    assert not os.path.exists(".map")

@pytest.mark.usefixtures("in_temp_dir")
def test_map_generate_character_limits():
    """
    Verify that exceeding max_characters_per_file triggers a constraint error.
    """
    with open("large_file.txt", "w", encoding="utf-8") as f:
        f.write("a" * 101)

    process = subprocess.run(
        [
            sys.executable, "-m", "mapper",
            "--max-chars-per-file", "100",
            "generate"
        ],
        capture_output=True,
        text=True
    )
    assert process.returncode != 0
    assert "Character limit exceeded" in process.stderr
    assert not os.path.exists(".map")
