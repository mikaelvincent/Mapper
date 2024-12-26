import os
import subprocess
import sys
import pytest

def test_map_generate_creates_default_map(tmp_path):
    """
    Validate that 'map generate' produces a .map file by default,
    respecting minimal rules. No symlinks or large files here.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
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
        # Basic checks for content presence
        assert "main.py" in map_content
        # Check that mapper-related files do not appear
        # by default (none were created here except .map)
    finally:
        os.chdir(original_dir)

def test_map_generate_respects_output_flag(tmp_path):
    """
    Verify that specifying --output writes to the given filename.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
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
    finally:
        os.chdir(original_dir)

@pytest.mark.skipif(
    not hasattr(sys, "platform") or "win" not in sys.platform.lower(),
    reason="Clipboard test primarily for Windows; cross-platform library might handle others."
)
def test_map_generate_clipboard_option(tmp_path):
    """
    Confirm that --clipboard attempts to copy the output to the clipboard.
    On non-Windows systems, this may behave differently depending on library support.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
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
        # The command should not fail; the presence of 'pyperclip' is assumed
        # Potentially could fail if clipboard is not accessible, in which case
        # the code logs an error message but does not crash.
        assert process.returncode == 0
        assert os.path.exists(".map")
    finally:
        os.chdir(original_dir)

def test_map_generate_symlink_halts(tmp_path):
    """
    Check that encountering a symlink causes the process to halt with error.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        with open("file.txt", "w", encoding="utf-8") as f:
            f.write("Some content")

        # Create a symlink if supported
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
    finally:
        os.chdir(original_dir)

def test_map_generate_file_limits(tmp_path):
    """
    Verify that exceeding max_files triggers a constraint error.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        for i in range(3):
            with open(f"file_{i}.txt", "w", encoding="utf-8") as f:
                f.write("content")

        # Pass --max-files=2 to override config
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
    finally:
        os.chdir(original_dir)

def test_map_generate_character_limits(tmp_path):
    """
    Verify that exceeding max_characters_per_file triggers a constraint error.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create a file with 101 characters
        with open("large_file.txt", "w", encoding="utf-8") as f:
            f.write("a" * 101)

        # Pass --max-chars-per-file=100
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
    finally:
        os.chdir(original_dir)
