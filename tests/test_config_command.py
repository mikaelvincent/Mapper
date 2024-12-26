import os
import subprocess
import sys
import pytest

def test_map_config_creates_mapconfig(tmp_path):
    """
    Verify that 'map config' creates the .mapconfig file if absent,
    and sets a given key=value pair.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Confirm file does not exist initially
        config_file = ".mapconfig"
        assert not os.path.exists(config_file), f"{config_file} should not exist yet."

        # Run the command with one --set pair
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper", "config",
                "--set", "ignore_hidden=true"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0, f"map config exited with code {process.returncode}"

        # Check that .mapconfig was created
        assert os.path.exists(config_file), f"{config_file} should exist after map config."
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "ignore_hidden=true" in content, "Expected ignore_hidden=true in .mapconfig."
    finally:
        os.chdir(original_dir)

def test_map_config_updates_existing_key(tmp_path):
    """
    Verify that 'map config' updates an existing key in .mapconfig.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    config_file = ".mapconfig"
    initial_content = """# Mapper configuration file
ignore_hidden=false
max_files=100
"""
    try:
        # Pre-create .mapconfig
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        # Update ignore_hidden
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper", "config",
                "--set", "ignore_hidden=true"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0

        # Verify update
        with open(config_file, "r", encoding="utf-8") as f:
            final_content = f.read()
        assert "ignore_hidden=true" in final_content
        assert "max_files=100" in final_content
    finally:
        os.chdir(original_dir)

def test_map_config_invalid_int_value(tmp_path):
    """
    Check graceful handling of an invalid integer value for max_files.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper", "config",
                "--set", "max_files=not_an_int"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        # The command should skip setting this invalid value
        assert "Invalid integer for max_files" in process.stdout
        config_file = ".mapconfig"
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                final_content = f.read()
            # Should not contain the invalid line
            assert "max_files=not_an_int" not in final_content
    finally:
        os.chdir(original_dir)

def test_map_config_unrecognized_key(tmp_path):
    """
    Unrecognized keys should be accepted as string values.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper", "config",
                "--set", "my_custom_setting=foo"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        config_file = ".mapconfig"
        assert os.path.exists(config_file)

        with open(config_file, "r", encoding="utf-8") as f:
            final_content = f.read()
        assert "my_custom_setting=foo" in final_content
    finally:
        os.chdir(original_dir)

def test_map_config_no_valid_pairs(tmp_path):
    """
    If no valid --set pairs are provided, .mapconfig should not be written.
    """
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        process = subprocess.run(
            [
                sys.executable, "-m", "mapper", "config",
                "--set", "invalidpairs"
            ],
            capture_output=True,
            text=True
        )
        assert process.returncode == 0
        assert "No valid configuration changes found." in process.stdout
        # .mapconfig should not exist because the pair is invalid
        assert not os.path.exists(".mapconfig")
    finally:
        os.chdir(original_dir)
