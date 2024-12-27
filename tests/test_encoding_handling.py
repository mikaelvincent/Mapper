import os
import sys
import pytest
import subprocess

@pytest.mark.parametrize("encoding_used,content", [
    ("utf-8", "UTF-8 content"),
    ("utf-16", "UTF-16 content"),
    ("latin-1", "Latin-1 content"),
])
def test_map_generate_with_various_encodings(tmp_path, encoding_used, content):
    """
    Validate that 'map generate' can read files encoded in different encodings.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Write .mapconfig with specific encodings (include utf-8, utf-16, latin-1)
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("# Mapper configuration file\n")
            f.write("encodings=utf-8,utf-16,latin-1\n")

        file_name = f"example_{encoding_used}.txt"
        # Create a file in the specified encoding
        with open(file_name, "w", encoding=encoding_used) as f:
            f.write(content)

        # Run 'map generate'
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, f"map generate failed for {encoding_used}"
        assert os.path.exists(".map"), ".map file should be created"

        # Verify .map contains the file name and its content (unless minimal_output is True)
        with open(".map", "r", encoding="utf-8") as map_file:
            map_content = map_file.read()
            # The file name must appear in the output tree
            assert file_name in map_content, f"Expected {file_name} in .map"
            # The file's content should also appear
            assert content in map_content, f"Expected file content in .map for {encoding_used}"

    finally:
        os.chdir(original_dir)


def test_map_generate_with_unrecognized_encoding_fallback(tmp_path):
    """
    Validate that an unrecognized encoding is skipped, falling back to available encodings
    without causing an error.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Write .mapconfig with an invalid encoding first, then valid encodings
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("# Mapper configuration file\n")
            f.write("encodings=invalid-enc,utf-8\n")

        file_name = "example_fallback.txt"
        content = "Fallback test content"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed with fallback"
        assert os.path.exists(".map"), ".map file should be created"

        with open(".map", "r", encoding="utf-8") as map_file:
            map_content = map_file.read()
            assert file_name in map_content, "Expected file name in .map"
            assert content in map_content, "Expected file content in .map after fallback"

    finally:
        os.chdir(original_dir)
