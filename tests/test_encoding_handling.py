import os
import sys
import pytest
import subprocess

@pytest.mark.usefixtures("in_temp_dir")
class TestEncodingHandling:
    def test_map_generate_forced_encoding(self, in_temp_dir):
        """
        Validate that 'map generate' uses a forced encoding if specified.
        """
        # Create a custom config with force_encoding
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("force_encoding=utf-8\n")

        file_name = "forced_encoding.txt"
        with open(file_name, "wb") as f:
            # Write data that is valid UTF-8
            f.write("Forced encoding content".encode("utf-8"))

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed with forced UTF-8"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as map_file:
            map_content = map_file.read()
            assert file_name in map_content
            assert "Forced encoding content" in map_content

    def test_map_generate_automatic_detection_success(self, in_temp_dir):
        """
        Validate that 'map generate' automatically detects encoding with chardet
        and includes the file content.
        """
        # No force_encoding in .mapconfig
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("# No forced encoding")

        file_name = "auto_detection.txt"
        with open(file_name, "wb") as f:
            # Write data in UTF-16
            f.write("Automatic detection content".encode("utf-16"))

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed with detection"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as map_file:
            map_content = map_file.read()
            assert file_name in map_content
            assert "Automatic detection content" in map_content

    def test_map_generate_automatic_detection_failure(self, in_temp_dir):
        """
        Validate that an ambiguous or unreadable file triggers an error.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("# No forced encoding")

        # Write some deliberately odd data to cause detection failure.
        # Using a repeated sequence of random bytes that should not match
        # any standard encoding with high confidence.
        file_name = "invalid_detection.dat"
        with open(file_name, "wb") as f:
            f.write(b"\xFE\xED\xFA\xCE" * 10)

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        # We expect chardet to fail or return a confidence < 0.5,
        # thus causing the Mapper process to exit with a non-zero return code.
        assert process.returncode != 0, "map generate should fail on detection error"

        # Accept either "detection failed", "confidence too low", or "Failed to decode".
        stderr_lower = process.stderr.lower()
        valid_failure_substrings = ["detection failed", "confidence too low", "failed to decode"]
        # Confirm at least one of these phrases is present in stderr:
        assert any(msg in stderr_lower for msg in valid_failure_substrings), \
            f"Expected detection failure message, got: {process.stderr}"

        assert not os.path.exists(".map"), ".map should not be created on failure"
