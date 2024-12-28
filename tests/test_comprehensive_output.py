import os
import sys
import pytest
import subprocess
from pathlib import Path


@pytest.mark.usefixtures("in_temp_dir")
class TestBasicOutput:
    def test_default_map_generation(self):
        """
        1.1 Default .map Generation
        Description: Ensure that invoking 'map generate' in a directory with a few text files
        creates a '.map' file containing the directory structure and file contents.
        Purpose: Validate the standard workflow and default settings.
        """
        # Create sample text files
        with open("file1.txt", "w", encoding="utf-8") as f:
            f.write("File 1 content")
        with open("file2.txt", "w", encoding="utf-8") as f:
            f.write("File 2 content")

        # Run 'map generate'
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"

        # Check .map content
        with open(".map", "r", encoding="utf-8") as map_file:
            map_content = map_file.read()
            assert "file1.txt" in map_content, "Expected file1.txt in .map"
            assert "file2.txt" in map_content, "Expected file2.txt in .map"
            assert "File 1 content" in map_content, "Expected file1.txt content in .map"
            assert "File 2 content" in map_content, "Expected file2.txt content in .map"

    def test_custom_output_filename(self):
        """
        1.2 Custom Output Filename
        Description: Run 'map generate' with --output set to a custom filename and
        verify that the specified file is created with the expected content.
        Purpose: Confirm that custom filenames are respected and do not overwrite .map.
        """
        custom_output = "my_map_output.txt"
        with open("sample.txt", "w", encoding="utf-8") as f:
            f.write("Sample content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate", "--output", custom_output],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(custom_output), f"{custom_output} should be created"

        with open(custom_output, "r", encoding="utf-8") as f:
            result = f.read()
        assert "sample.txt" in result, "Expected sample.txt in custom map output"
        assert "Sample content" in result, "Expected sample content in custom map output"

    def test_minimal_output_flag(self):
        """
        1.3 Minimal Output Flag
        Description: Execute 'map generate' with --minimal-output=true and confirm that the
        generated file only includes file names (no file contents).
        Purpose: Verify that minimal output configuration is honored.
        """
        with open("minimal.txt", "w", encoding="utf-8") as f:
            f.write("Should not appear in minimal output")

        process = subprocess.run(
            [
                sys.executable, "-m", "mapper",
                "--minimal-output", "true",
                "generate"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"

        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "minimal.txt" in content, "File name should appear in minimal output"
        assert "Should not appear in minimal output" not in content, \
            "File contents must not appear in minimal output mode"

    @pytest.mark.skipif(
        not hasattr(sys, "platform") or "win" not in sys.platform.lower(),
        reason="Clipboard test primarily for Windows; cross-platform library might handle others."
    )
    def test_clipboard_copy(self):
        """
        1.4 Clipboard Copy
        Description: Run 'map generate' with --clipboard on supported systems
        to validate copying to the clipboard.
        Purpose: Check compatibility with pyperclip and ensure no errors occur if copying fails.
        """
        with open("clipboard_test.txt", "w", encoding="utf-8") as f:
            f.write("Clipboard content")

        process = subprocess.run(
            [
                sys.executable, "-m", "mapper",
                "generate", "--clipboard"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate with clipboard should succeed"
        assert os.path.exists(".map"), ".map file should be created"

    def test_empty_directory_handling(self):
        """
        1.5 Empty Directory Handling
        Description: Generate a .map in an empty directory to confirm that it gracefully
        includes only the directory name and produces minimal content.
        Purpose: Guarantee correct behavior in edge cases where no files exist.
        """
        # No files created
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed in empty directory"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        # Expect minimal content
        assert len(content.strip()) > 0, "Should contain at least the directory label"


@pytest.mark.usefixtures("in_temp_dir")
class TestConfigurationMerging:
    def test_configuration_merging_precedence(self):
        """
        2.1 Configuration Merging Precedence
        Description: Create a .mapconfig that sets specific values and override them via CLI flags.
        Purpose: Validate merging layers: defaults < file config < CLI overrides.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("max_files=1\n")
            f.write("ignore_hidden=true\n")

        # Create more than one file and a hidden file
        with open("file1.txt", "w", encoding="utf-8") as f:
            f.write("File 1 content")
        with open(".hiddenfile", "w", encoding="utf-8") as f:
            f.write("Hidden content")
        with open("file2.txt", "w", encoding="utf-8") as f:
            f.write("File 2 content")

        # Override ignore_hidden=False via CLI, also override max_files=None
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper",
                "--ignore-hidden", "false",
                "--max-files", "None",
                "generate"
            ],
            capture_output=True,
            text=True
        )
        # Expect success, no constraint violation, hidden file included
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert ".hiddenfile" in content, "Hidden file should be included due to CLI override"
        assert "File 2 content" in content, "Second file not limited by max_files=1"

    def test_unrecognized_configuration_keys(self):
        """
        2.3 Unrecognized Configuration Keys
        Description: Define a custom key in .mapconfig and confirm that it is preserved
        while having no effect on Mapper’s main functionalities.
        Purpose: Check that unexpected keys do not break the parser.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("custom_key=123\n")
            f.write("ignore_hidden=false\n")

        with open("demo.txt", "w", encoding="utf-8") as f:
            f.write("Demo content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"

        # Confirm the file is recognized or at least not broken
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "demo.txt" in content, "Demo file should be included"
        # The 'custom_key' has no direct effect, but no errors should occur


@pytest.mark.usefixtures("in_temp_dir")
class TestFileInclusionExclusion:
    def test_ignore_hidden_files(self):
        """
        3.1 Ignore Hidden Files
        Description: Place hidden files in a directory. Confirm that map generate excludes them
        by default if ignore_hidden is true, and includes them if set to false.
        Purpose: Validate that hidden files are properly skipped or included upon override.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("ignore_hidden=true\n")
        with open("file.txt", "w", encoding="utf-8") as f:
            f.write("Visible content")
        with open(".secret", "w", encoding="utf-8") as f:
            f.write("Secret content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "file.txt" in content, "Visible file should appear"
        assert ".secret" not in content, "Hidden file should not appear by default"

        # Now override ignore_hidden=false
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper",
                "--ignore-hidden", "false",
                "generate"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed with override"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert ".secret" in content, "Hidden file should now appear due to CLI override"

    def test_mapignore_mapomit(self):
        """
        3.2 .mapignore and .mapomit
        Description: Populate .mapignore and .mapomit with patterns and confirm that ignored files
        are excluded, while omitted files appear as [omitted].
        Purpose: Ensure that .mapignore overrides default inclusions, and .mapomit masks contents.
        """
        with open(".mapignore", "w", encoding="utf-8") as f:
            f.write("ignore_me.txt\n")
        with open(".mapomit", "w", encoding="utf-8") as f:
            f.write("omit_me.txt\n")

        with open("ignore_me.txt", "w", encoding="utf-8") as f:
            f.write("This file should be ignored entirely.")
        with open("omit_me.txt", "w", encoding="utf-8") as f:
            f.write("This file should be included, but with [omitted] content.")
        with open("include_me.txt", "w", encoding="utf-8") as f:
            f.write("Should appear in .map with content.")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        assert os.path.exists(".map"), ".map file should be created"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "ignore_me.txt" not in content, "File in .mapignore must be excluded"
        assert "omit_me.txt" in content, "File in .mapomit must be listed"
        assert "[omitted]" in content, "Omitted file content must appear as [omitted]"
        assert "include_me.txt" in content, "Included file should appear with content"
        assert "Should appear in .map with content." in content, "File content should appear"


@pytest.mark.usefixtures("in_temp_dir")
class TestTraversalConstraints:
    def test_symlink_detection(self):
        """
        4.1 Symlink Detection
        Description: Add a symbolic link to a file and confirm that map generate aborts
        with a SymlinkEncounteredError.
        Purpose: Validate safety mechanisms to avoid unexpected symlinks.
        """
        with open("real_file.txt", "w", encoding="utf-8") as f:
            f.write("Real file content")
        if not hasattr(os, "symlink"):
            pytest.skip("Symlinks not supported on this platform.")
        os.symlink("real_file.txt", "link_to_file")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode != 0, "Should fail upon encountering a symlink"
        assert "Symlink found" in process.stderr, "Expected symlink error message"

    def test_file_count_limits(self):
        """
        4.2 File Count Limits
        Description: Specify max_files and verify that exceeding the limit triggers an error.
        Purpose: Ensure the enforced file limit constraints.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("max_files=1\n")

        # Create two files
        with open("file1.txt", "w", encoding="utf-8") as f:
            f.write("content")
        with open("file2.txt", "w", encoding="utf-8") as f:
            f.write("content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode != 0, "Should fail due to exceeding file limit"
        assert "File limit exceeded" in process.stderr, "Expected file limit exceeded error"

    def test_character_count_limits(self):
        """
        4.3 Character Count Limits
        Description: Set max_characters_per_file to a low number and create an oversized file.
        Purpose: Confirm that map generate fails and outputs a ConstraintViolatedError.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("max_characters_per_file=10\n")

        with open("big_file.txt", "w", encoding="utf-8") as f:
            f.write("0123456789ABCDEF")  # More than 10 characters

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode != 0, "Should fail due to exceeding character limit"
        assert "Character limit exceeded" in process.stderr, "Expected constraint violation error"

    def test_directory_recursion(self):
        """
        4.4 Directory Recursion
        Description: Create a nested directory structure and confirm that map generate
        displays the hierarchy with proper folder prefixes.
        Purpose: Validate recursive traversal and accurate visual representation.
        """
        os.mkdir("level1")
        with open(os.path.join("level1", "file1.txt"), "w", encoding="utf-8") as f:
            f.write("Level 1 content")
        os.mkdir(os.path.join("level1", "level2"))
        with open(os.path.join("level1", "level2", "file2.txt"), "w", encoding="utf-8") as f:
            f.write("Level 2 content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "level1" in content, "Nested directory should appear"
        assert "level2" in content, "Deeper directory should appear"
        assert "file2.txt" in content, "File in nested directory should be listed"

    def test_trimming_whitespace(self):
        """
        4.5 Trimming Whitespace
        Description: Enable trim_trailing_whitespaces and trim_all_empty_lines. Include
        files with trailing spaces and multiple blank lines. Confirm that output is trimmed.
        Purpose: Verify correctness of optional whitespace rules.
        """
        with open(".mapconfig", "w", encoding="utf-8") as f:
            f.write("trim_trailing_whitespaces=true\n")
            f.write("trim_all_empty_lines=true\n")

        with open("whitespace.txt", "w", encoding="utf-8") as f:
            f.write("Line with trailing spaces    \n\n\nAnother line\n")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        with open(".map", "r", encoding="utf-8") as f:
            output = f.read()
        # Expect no trailing spaces and no entirely blank lines
        assert "trailing spaces   " not in output, "Trailing spaces should be trimmed"
        assert "\n\n\n" not in output, "All empty lines should be removed"


@pytest.mark.usefixtures("in_temp_dir")
class TestHeaderFooter:
    def test_mapheader_content(self):
        """
        6.1 .mapheader Content
        Description: Create a .mapheader with custom text and confirm that map generate
        inserts it at the top of .map followed by a triple dash.
        Purpose: Validate correct inclusion of user-defined headers.
        """
        with open(".mapheader", "w", encoding="utf-8") as f:
            f.write("CUSTOM HEADER")
        with open("somefile.txt", "w", encoding="utf-8") as f:
            f.write("Content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, "map generate should succeed"
        with open(".map", "r", encoding="utf-8") as f:
            generated = f.read()
        assert generated.startswith("CUSTOM HEADER"), "Header should appear at the top"
        assert "---" in generated, "Triple dash should follow header"

    def test_mapfooter_content(self):
        """
        6.2 .mapfooter Content
        Description: Create a .mapfooter with custom text and verify that map generate
        appends it at the end of .map.
        Purpose: Ensure that the footer is added after file sections.
        """
        with open(".mapfooter", "w", encoding="utf-8") as f:
            f.write("CUSTOM FOOTER")
        with open("somefile.txt", "w", encoding="utf-8") as f:
            f.write("Content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        with open(".map", "r", encoding="utf-8") as f:
            generated = f.read()
        assert generated.rstrip().endswith("CUSTOM FOOTER"), "Footer should appear at the end"

    def test_absent_header_footer(self):
        """
        6.3 Absent Header/Footer
        Description: Remove or rename .mapheader and .mapfooter and confirm that map generate
        completes without adding these sections.
        Purpose: Check that missing files do not cause errors.
        """
        # Just ensure they don't exist
        if os.path.exists(".mapheader"):
            os.remove(".mapheader")
        if os.path.exists(".mapfooter"):
            os.remove(".mapfooter")

        with open("file.txt", "w", encoding="utf-8") as f:
            f.write("Content")

        process = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        with open(".map", "r", encoding="utf-8") as f:
            generated = f.read()
        assert "CUSTOM HEADER" not in generated, "Should not contain any header"
        assert "CUSTOM FOOTER" not in generated, "Should not contain any footer"


@pytest.mark.usefixtures("in_temp_dir")
class TestInitializationAndConfiguration:
    def test_mapper_version_check(self):
        """
        7.3 Mapper Version Check
        Description: Run 'map version' to confirm that CLI displays the __version__ string.
        Purpose: Ensure accurate representation of the application version.
        """
        process = subprocess.run(
            [sys.executable, "-m", "mapper", "version"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        # The default version is 0.1.0 in mapper/__init__.py
        assert "Mapper version: 0.1.0" in process.stdout, "Expected version in output"

    def test_full_workflow_init_to_generate(self):
        """
        9.3 Workflow from map init to map generate
        Description: Start with an empty directory, run 'map init', then manually modify
        the generated files and conclude with 'map generate'. Confirm final .map correctness.
        Purpose: Test a real-world scenario of typical project setup and usage.
        """
        # Step 1: map init
        process_init = subprocess.run(
            [sys.executable, "-m", "mapper", "init"],
            capture_output=True,
            text=True
        )
        assert process_init.returncode == 0, "map init should succeed"

        # Modify some files
        with open(".mapheader", "w", encoding="utf-8") as f:
            f.write("INIT HEADER")
        with open(".mapfooter", "w", encoding="utf-8") as f:
            f.write("INIT FOOTER")

        # Create a content file
        with open("hello.txt", "w", encoding="utf-8") as f:
            f.write("Hello World")

        # Step 2: map generate
        process_gen = subprocess.run(
            [sys.executable, "-m", "mapper", "generate"],
            capture_output=True,
            text=True
        )
        assert process_gen.returncode == 0, "map generate should succeed"

        with open(".map", "r", encoding="utf-8") as f:
            content = f.read()
        assert "INIT HEADER" in content, "Header should be included"
        assert "INIT FOOTER" in content, "Footer should be included"
        assert "hello.txt" in content, "File should be listed"
        assert "Hello World" in content, "File content should be included"
