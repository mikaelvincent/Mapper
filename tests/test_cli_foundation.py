import subprocess
import sys

def test_cli_help_command():
    """Test that the 'map help' command returns placeholder help content."""
    process = subprocess.run([sys.executable, "-m", "mapper", "help"], capture_output=True, text=True)
    assert process.returncode == 0
    assert "Placeholder help content" in process.stdout

def test_cli_version_command():
    """Test that the 'map version' command returns the current version content."""
    process = subprocess.run([sys.executable, "-m", "mapper", "version"], capture_output=True, text=True)
    assert process.returncode == 0
    assert "Mapper version: 0.1.0" in process.stdout
