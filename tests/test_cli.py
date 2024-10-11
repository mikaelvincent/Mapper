import pytest
from click.testing import CliRunner
from mapper.cli import main
import os
import tempfile
import shutil
from unittest.mock import patch

@pytest.fixture
def temp_config_file(monkeypatch):
    """Create a temporary config file and patch CONFIG_FILE path."""
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        config_file = tf.name
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

def test_version():
    """Test that 'version' command outputs the correct version."""
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Mapper version' in result.output

def test_help_command():
    """Test that 'help' command displays help message."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'Commands:' in result.output

def test_generate_default(temp_config_file):
    """Test 'generate' command with default settings."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure '.map' is created
        assert os.path.exists('.map')

def test_generate_with_custom_output(temp_config_file):
    """Test 'generate' command with custom output file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'custom_.map'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure 'custom_.map' is created
        assert os.path.exists('custom_.map')

def test_reset_settings(temp_config_file):
    """Test 'reset-settings' command resets settings to default."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a dummy settings file
        with open(temp_config_file, 'w') as f:
            f.write('{}')
        result = runner.invoke(main, ['reset-settings'])
        assert result.exit_code == 0
        assert 'Settings have been reset to default values.' in result.output
        # Ensure the settings file is removed
        assert not os.path.exists(temp_config_file)

def test_save_settings(temp_config_file):
    """Test that settings are saved when '--save-settings' is used."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        assert result.exit_code == 0
        assert os.path.exists(temp_config_file)
        with open(temp_config_file, 'r') as f:
            settings = f.read()
        assert '"output": "custom_.map"' in settings

def test_load_settings(temp_config_file):
    """Test that settings are loaded when '--load-settings' is used."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Save settings first
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        # Now load settings and generate without specifying output
        result = runner.invoke(main, ['--load-settings', 'generate'])
        assert result.exit_code == 0
        # Ensure 'custom_.map' is created, indicating that the output setting was loaded
        assert os.path.exists('custom_.map')

def test_save_and_load_settings(temp_config_file):
    """Test behavior when both '--save-settings' and '--load-settings' are used."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Save settings with custom output
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        # Now modify settings and save and load at the same time
        result = runner.invoke(main, ['--save-settings', '--load-settings', 'generate', '--output', 'another_.map'])
        assert result.exit_code == 0
        # Check that settings have been updated
        with open(temp_config_file, 'r') as f:
            settings = f.read()
        assert '"output": "another_.map"' in settings
        # Ensure 'another_.map' is created
        assert os.path.exists('another_.map')

def test_generate_with_custom_ignore_file(temp_config_file):
    """Test 'generate' command with custom ignore file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create some files
        os.makedirs('test_dir')
        with open('test_dir/keep.txt', 'w') as f:
            f.write('keep')
        with open('test_dir/ignore.txt', 'w') as f:
            f.write('ignore')
        # Create a .mapignore file
        with open('.mapignore', 'w') as f:
            f.write('ignore.txt\n')
        # Run generate
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        # Read the generated .map file
        with open('.map', 'r') as f:
            output = f.read()
        # Check that 'ignore.txt' is not included in the output
        assert 'ignore.txt' not in output
        # Check that 'keep.txt' is included
        assert 'keep.txt' in output

def test_generate_with_custom_omit_file(temp_config_file):
    """Test 'generate' command with custom omit file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create some files
        os.makedirs('test_dir')
        with open('test_dir/keep.txt', 'w') as f:
            f.write('keep')
        with open('test_dir/omit.txt', 'w') as f:
            f.write('omit')
        # Create a .mapomit file
        with open('.mapomit', 'w') as f:
            f.write('omit.txt\n')
        # Run generate
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        # Read the generated .map file
        with open('.map', 'r') as f:
            output = f.read()
        # Check that 'omit.txt' is included but marked as omitted
        assert 'omit.txt' in output
        assert '[omitted]' in output
        # Check that 'keep.txt' is included and not omitted
        assert 'keep.txt' in output

def test_generate_output_content(temp_config_file):
    """Test that the generated '.map' file contains the correct structure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a directory structure
        os.makedirs('dir/subdir')
        with open('dir/subdir/file.txt', 'w') as f:
            f.write('content')
        # Run generate
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        # Read the '.map' file
        with open('.map', 'r') as f:
            output = f.read()
        # Check that the directory structure is represented
        assert '-> dir' in output
        assert '-> subdir' in output
        assert '-> file.txt' in output

def test_generate_with_ignore_hidden(temp_config_file):
    """Test 'generate' command with '--ignore-hidden' option set to false."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create hidden and visible files
        with open('.hidden_file', 'w') as f:
            f.write('hidden')
        with open('visible_file', 'w') as f:
            f.write('visible')
        # Run generate with '--ignore-hidden false'
        result = runner.invoke(main, ['generate', '--ignore-hidden', 'false'])
        assert result.exit_code == 0
        # Read the generated '.map' file
        with open('.map', 'r') as f:
            output = f.read()
        # Check that '.hidden_file' is included in the output
        assert '.hidden_file' in output
        assert 'visible_file' in output

def test_generate_with_hidden_files(temp_config_file):
    """Test 'generate' command with hidden files present."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create hidden and non-hidden files
        with open('.hidden_file', 'w') as f:
            f.write('hidden')
        with open('visible_file', 'w') as f:
            f.write('visible')
        # Run generate with default settings (ignore-hidden = True)
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        # Check that '.hidden_file' is not included
        assert '.hidden_file' not in output
        # Check that 'visible_file' is included
        assert 'visible_file' in output

def test_generate_with_max_size(temp_config_file):
    """Test 'generate' command with '--max-size' option."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a large file
        with open('large_file.txt', 'w') as f:
            f.write('a' * 2000)
        # Run generate with max-size 1000
        result = runner.invoke(main, ['generate', '--max-size', '1000'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        # Check that content is truncated
        assert '... [Truncated]' in output

def test_generate_with_header_and_footer(temp_config_file):
    """Test 'generate' command with header and footer files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create header and footer files
        with open('header.txt', 'w') as f:
            f.write('Header Content')
        with open('footer.txt', 'w') as f:
            f.write('Footer Content')
        # Run generate with header and footer
        result = runner.invoke(main, ['generate', '--header', 'header.txt', '--footer', 'footer.txt'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        # Check that header and footer are included
        assert 'Header Content' in output
        assert 'Footer Content' in output

def test_generate_with_verbose_and_quiet(temp_config_file):
    """Test 'generate' command with '--verbose' and '--quiet' options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Run generate with '--verbose'
        result = runner.invoke(main, ['--verbose', 'generate'])
        assert result.exit_code == 0
        # Since implementation doesn't output extra verbose messages, we can check exit code
        # Run generate with '--quiet'
        result = runner.invoke(main, ['--quiet', 'generate'])
        assert result.exit_code == 0
        # Ensure that 'Project structure generated' is not printed
        assert 'Project structure generated' not in result.output

def test_invalid_subcommand():
    """Test that invalid subcommands return an error."""
    runner = CliRunner()
    result = runner.invoke(main, ['invalid'])
    assert result.exit_code != 0
    assert 'No such command' in result.output

def test_generate_with_invalid_option():
    """Test 'generate' command with invalid option."""
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--nonexistent-option'])
    assert result.exit_code != 0
    assert 'Error' in result.output

def test_generate_with_verbose_and_quiet_together(temp_config_file):
    """Test 'generate' command with both '--verbose' and '--quiet' options."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--verbose', '--quiet', 'generate'])
        assert result.exit_code == 0
        # '--quiet' suppresses output
        assert 'Project structure generated' not in result.output

def test_load_settings_with_invalid_config(temp_config_file):
    """Test behavior when config file is invalid."""
    # Write invalid JSON to config file
    with open(temp_config_file, 'w') as f:
        f.write('invalid json')
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--load-settings', 'generate'])
        # Should proceed with default settings
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output

def test_generate_with_unwritable_output(temp_config_file):
    """Test 'generate' command when output file cannot be written."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Mock open to raise an IOError when attempting to write
        def mock_open(*args, **kwargs):
            raise IOError("Permission denied")
        with patch('builtins.open', mock_open):
            result = runner.invoke(main, ['generate'])
            assert result.exit_code != 0
            assert 'Permission denied' in result.output

def test_generate_with_nonexistent_output_dir(temp_config_file):
    """Test 'generate' command with output file in nonexistent directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'nonexistent_dir/output.map'])
        assert result.exit_code != 0
        assert 'No such file or directory' in result.output or 'Error' in result.output

def test_load_settings_with_overrides(temp_config_file):
    """Test that command-line options override loaded settings."""
    # Save settings with custom output
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'saved_output.map'])
        # Now load settings but override output
        result = runner.invoke(main, ['--load-settings', 'generate', '--output', 'override_output.map'])
        assert result.exit_code == 0
        # Ensure 'override_output.map' is created
        assert os.path.exists('override_output.map')
        # Ensure 'saved_output.map' is not created
        assert not os.path.exists('saved_output.map')

def test_generate_with_symlinks(temp_config_file):
    """Test 'generate' command in presence of symlinks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('dir')
        with open('dir/file.txt', 'w') as f:
            f.write('content')
        
        # Check if the OS supports symlinks and if the current user has the necessary permissions
        symlink_supported = hasattr(os, 'symlink')
        is_windows = os.name == 'nt'
        can_create_symlink = False

        if symlink_supported:
            try:
                # Attempt to create a symlink to check if it's permitted
                os.symlink('dir', 'link_to_dir')
                can_create_symlink = True
            except (OSError, NotImplementedError, AttributeError) as e:
                can_create_symlink = False

        if can_create_symlink:
            # Run generate command
            result = runner.invoke(main, ['generate'])
            assert result.exit_code == 0, f"Generate command failed with exit code {result.exit_code}"
            with open('.map', 'r') as f:
                output = f.read()
            # Check that symlink is included in the output
            assert '-> link_to_dir' in output, "Symlink 'link_to_dir' not found in output."
        else:
            # Symlinks are not supported or cannot be created; skip the test
            pytest.skip("Symlinks not supported or insufficient privileges on this platform.")


def test_generate_with_non_utf8_file(temp_config_file):
    """Test 'generate' command with files of non-UTF-8 encoding."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a file with non-UTF-8 encoding
        with open('binary_file', 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')
        # Run generate
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        # Check that '[Content Unreadable]' is included
        assert '[Content Unreadable]' in output

def test_generate_with_special_characters_in_filenames(temp_config_file):
    """Test 'generate' command with filenames containing special characters."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        filename = 'spécial_文件.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('content')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r', encoding='utf-8') as f:
            output = f.read()
        assert filename in output

def test_generate_with_large_directory_structure(temp_config_file):
    """Test 'generate' command with a large directory structure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a large directory structure
        for i in range(10):
            dir_name = f'dir_{i}'
            os.makedirs(dir_name)
            for j in range(10):
                file_name = os.path.join(dir_name, f'file_{j}.txt')
                with open(file_name, 'w') as f:
                    f.write('content')
        # Run generate
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        # Check that output includes all directories and files
        with open('.map', 'r') as f:
            output = f.read()
        for i in range(10):
            dir_name = f'dir_{i}'
            assert dir_name in output
            for j in range(10):
                file_name = f'file_{j}.txt'
                assert file_name in output
