import pytest
from click.testing import CliRunner
from mapper.cli.main import main
import os
import tempfile
import shutil
from unittest.mock import patch

@pytest.fixture
def temp_config_file(monkeypatch):
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        config_file = tf.name
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

def test_generate_default(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        assert os.path.exists('.map')

def test_generate_with_custom_output(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'custom_.map'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        assert os.path.exists('custom_.map')

def test_save_settings(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        assert result.exit_code == 0
        assert os.path.exists(temp_config_file)
        with open(temp_config_file, 'r') as f:
            settings = f.read()
        assert '"output": "custom_.map"' in settings

def test_load_settings(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        result = runner.invoke(main, ['--load-settings', 'generate'])
        assert result.exit_code == 0
        assert os.path.exists('custom_.map')

def test_save_and_load_settings(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        result = runner.invoke(main, ['--save-settings', '--load-settings', 'generate', '--output', 'another_.map'])
        assert result.exit_code == 0
        with open(temp_config_file, 'r') as f:
            settings = f.read()
        assert '"output": "another_.map"' in settings
        assert os.path.exists('another_.map')
        assert not os.path.exists('custom_.map')

def test_generate_with_custom_ignore_file(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('test_dir')
        with open('test_dir/keep.txt', 'w') as f:
            f.write('keep')
        with open('test_dir/ignore.txt', 'w') as f:
            f.write('ignore')
        with open('.mapignore', 'w') as f:
            f.write('ignore.txt\n')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert 'ignore.txt' not in output
        assert 'keep.txt' in output

def test_generate_with_custom_omit_file(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('test_dir')
        with open('test_dir/keep.txt', 'w') as f:
            f.write('keep')
        with open('test_dir/omit.txt', 'w') as f:
            f.write('omit')
        with open('.mapomit', 'w') as f:
            f.write('omit.txt\n')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert 'omit.txt' in output
        assert '[omitted]' in output
        assert 'keep.txt' in output

def test_generate_output_content(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('dir/subdir')
        with open('dir/subdir/file.txt', 'w') as f:
            f.write('content')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert '-> dir' in output
        assert '-> subdir' in output
        assert '-> file.txt' in output

def test_generate_with_ignore_hidden(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('.hidden_file', 'w') as f:
            f.write('hidden')
        with open('visible_file', 'w') as f:
            f.write('visible')
        result = runner.invoke(main, ['generate', '--ignore-hidden', 'false'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert '.hidden_file' in output
        assert 'visible_file' in output

def test_generate_with_hidden_files(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('.hidden_file', 'w') as f:
            f.write('hidden')
        with open('visible_file', 'w') as f:
            f.write('visible')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert '.hidden_file' not in output
        assert 'visible_file' in output

def test_generate_with_max_size(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('large_file.txt', 'w') as f:
            f.write('a' * 2000)
        result = runner.invoke(main, ['generate', '--max-size', '1000'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert '... [Truncated]' in output

def test_generate_with_header_and_footer(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('header.txt', 'w') as f:
            f.write('Header Content')
        with open('footer.txt', 'w') as f:
            f.write('Footer Content')
        with open('file.txt', 'w') as f:
            f.write('content')
        result = runner.invoke(main, ['generate', '--header', 'header.txt', '--footer', 'footer.txt'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert 'Header Content' in output
        assert 'Footer Content' in output

def test_generate_with_verbose_and_quiet(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--verbose', 'generate'])
        assert result.exit_code == 0
        result = runner.invoke(main, ['--quiet', 'generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' not in result.output

def test_generate_with_invalid_option(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--nonexistent-option'])
        assert result.exit_code != 0
        assert 'Error' in result.output

def test_generate_with_verbose_and_quiet_together(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--verbose', '--quiet', 'generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' not in result.output

def test_load_settings_with_invalid_config(temp_config_file):
    with open(temp_config_file, 'w') as f:
        f.write('invalid json')
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['--load-settings', 'generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output

def test_generate_with_unwritable_output(temp_config_file):
    def mock_open(*args, **kwargs):
        raise IOError("Permission denied")
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch('builtins.open', mock_open):
            result = runner.invoke(main, ['generate'])
            assert result.exit_code != 0
            assert 'Permission denied' in result.output

def test_generate_with_nonexistent_output_dir(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'nonexistent_dir/output.map'])
        assert result.exit_code != 0
        assert 'No such file or directory' in result.output or 'Error' in result.output

def test_load_settings_with_overrides(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ['--save-settings', 'generate', '--output', 'custom_.map'])
        result = runner.invoke(main, ['--save-settings', '--load-settings', 'generate', '--output', 'another_.map'])
        assert result.exit_code == 0
        with open(temp_config_file, 'r') as f:
            settings = f.read()
        assert '"output": "another_.map"' in settings
        assert os.path.exists('another_.map')
        assert not os.path.exists('custom_.map')

def test_generate_with_symlinks(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs('dir')
        with open('dir/file.txt', 'w') as f:
            f.write('content')
        try:
            os.symlink('dir', 'link_to_dir')
            can_create_symlink = True
        except (OSError, NotImplementedError, AttributeError):
            can_create_symlink = False
        if can_create_symlink:
            result = runner.invoke(main, ['generate'])
            assert result.exit_code == 0
            with open('.map', 'r') as f:
                output = f.read()
            assert '-> link_to_dir' in output
        else:
            pytest.skip("Symlinks not supported or insufficient privileges on this platform.")

def test_generate_with_non_utf8_file(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('binary_file', 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        assert '[Content Unreadable]' in output

def test_generate_with_special_characters_in_filenames(temp_config_file):
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
    runner = CliRunner()
    with runner.isolated_filesystem():
        for i in range(10):
            dir_name = f'dir_{i}'
            os.makedirs(dir_name)
            for j in range(10):
                file_name = os.path.join(dir_name, f'file_{j}.txt')
                with open(file_name, 'w') as f:
                    f.write('content')
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        with open('.map', 'r') as f:
            output = f.read()
        for i in range(10):
            dir_name = f'dir_{i}'
            assert dir_name in output
            for j in range(10):
                file_name = f'file_{j}.txt'
                assert file_name in output
