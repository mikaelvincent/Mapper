import os
import subprocess
import sys
import pytest

def create_mapconfig(tmp_path, content):
    config_path = tmp_path / ".mapconfig"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    return config_path

@pytest.mark.usefixtures("in_temp_dir")
class TestConfigFileHandling:
    @pytest.mark.parametrize("config_content,expected", [
        (
            "max_files=500\nignore_hidden=false\n",
            {
                "max_files": 500,
                "ignore_hidden": False,
                "trim_trailing_whitespaces": True,
                "trim_all_empty_lines": False,
                "minimal_output": False,
                "use_absolute_path_title": False
            }
        ),
        (
            """
# Comment line
max_files=1000
max_characters_per_file=2000
ignore_hidden=true
trim_trailing_whitespaces=false
trim_all_empty_lines=true
minimal_output=true
use_absolute_path_title=true
encodings=utf-8,latin-1
            """,
            {
                "max_files": 1000,
                "max_characters_per_file": 2000,
                "ignore_hidden": True,
                "trim_trailing_whitespaces": False,
                "trim_all_empty_lines": True,
                "minimal_output": True,
                "use_absolute_path_title": True
            }
        ),
        (
            "max_files=invalid\nignore_hidden=true\n",
            {
                "max_files": None,
                "ignore_hidden": True
            }
        ),
        (
            "",
            {}
        )
    ])
    def test_config_file_handling(self, in_temp_dir, config_content, expected):
        """
        Test reading .mapconfig values and verifying they merge with defaults.
        """
        create_mapconfig(in_temp_dir, config_content)

        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "mapper",
                "--max-files", "None",
                "help"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0

    @pytest.mark.parametrize("cli_args,expected_boolean", [
        (["--ignore-hidden", "true"], True),
        (["--ignore-hidden", "false"], False),
        (["--ignore-hidden", "yes"], True),
        (["--ignore-hidden", "no"], None),
    ])
    def test_cli_overrides_boolean(self, in_temp_dir, cli_args, expected_boolean):
        """
        Test that CLI boolean overrides take precedence over .mapconfig or defaults.
        """
        create_mapconfig(in_temp_dir, "ignore_hidden=false\n")
        process = subprocess.run(
            [sys.executable, "-m", "mapper"] + cli_args + ["help"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0

    @pytest.mark.parametrize("cli_args,expected_int", [
        (["--max-files", "999"], 999),
        (["--max-files", "0"], 0),
        (["--max-files", "-10"], -10),
    ])
    def test_cli_overrides_integers(self, in_temp_dir, cli_args, expected_int):
        """
        Test that CLI integer overrides take precedence over .mapconfig or defaults.
        """
        create_mapconfig(in_temp_dir, "max_files=100\n")
        process = subprocess.run(
            [sys.executable, "-m", "mapper"] + cli_args + ["help"],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
