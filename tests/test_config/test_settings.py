import pytest
import os
import tempfile
import json
from mapper.config.settings import save_user_settings, load_user_settings, reset_settings, DEFAULT_SETTINGS, CONFIG_FILE
from unittest.mock import patch
import shutil
import sys

@pytest.fixture
def temp_config_file(monkeypatch):
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        config_file = tf.name
    monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

@pytest.fixture
def temp_config_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, 'config_dir')
        os.makedirs(config_dir, exist_ok=True)
        monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', config_dir)
        yield config_dir

def test_default_settings():
    assert DEFAULT_SETTINGS == {
        'output': '.map',
        'ignore': '.mapignore',
        'header': '.mapheader',
        'footer': '.mapfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000000,
        'verbose': False,
        'quiet': False
    }

def test_save_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_.map',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '  ',
        'arrow': '-->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': False
    }
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = f.read()
    assert '"output": "custom_.map"' in loaded_settings
    assert '"ignore_hidden": false' in loaded_settings
    assert '"indent_char": "  "' in loaded_settings
    assert '"arrow": "-->"' in loaded_settings

def test_load_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_.map',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '  ',
        'arrow': '-->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': True
    }
    save_user_settings(settings)
    loaded_settings = load_user_settings()
    assert loaded_settings == settings

def test_load_user_settings_default(temp_config_file, monkeypatch):
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_save_user_settings_with_missing_keys(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_.map'
    }
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = f.read()
    assert '"output": "custom_.map"' in loaded_settings

def test_load_user_settings_with_partial_settings(temp_config_file, monkeypatch):
    partial_settings = {
        'output': 'custom_.map',
        'verbose': True
    }
    save_user_settings(partial_settings)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(partial_settings)
    assert loaded_settings == expected_settings

def test_load_user_settings_with_invalid_json(temp_config_file, monkeypatch):
    with open(temp_config_file, 'w') as f:
        f.write('invalid json')
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_reset_settings_removes_config_file(temp_config_file, monkeypatch):
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    assert os.path.exists(temp_config_file)
    reset_settings()
    assert not os.path.exists(temp_config_file)

def test_save_user_settings_overwrites_existing_file(temp_config_file, monkeypatch):
    initial_settings = {
        'output': 'initial_.map'
    }
    updated_settings = {
        'output': 'updated_.map'
    }
    save_user_settings(initial_settings)
    with open(temp_config_file, 'r') as f:
        data = f.read()
    assert data == json.dumps(initial_settings, indent=4)
    save_user_settings(updated_settings)
    with open(temp_config_file, 'r') as f:
        data = f.read()
    assert data == json.dumps(updated_settings, indent=4)

def test_save_user_settings_with_invalid_data(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_.map',
        'invalid_key': set([1, 2, 3])
    }
    with pytest.raises(TypeError):
        save_user_settings(settings)

def test_load_user_settings_with_incorrect_data_types(temp_config_file, monkeypatch):
    incorrect_settings = {
        'output': 123,
        'ignore_hidden': 'yes'
    }
    save_user_settings(incorrect_settings)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(incorrect_settings)
    assert loaded_settings == expected_settings

def test_save_user_settings_with_nonexistent_directory(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    non_existent_dir = os.path.join(temp_dir, 'nonexistent')
    config_file = os.path.join(non_existent_dir, 'config.json')
    monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', config_file)
    settings = {
        'output': 'custom_.map'
    }
    with pytest.raises(FileNotFoundError):
        save_user_settings(settings)
    os.rmdir(temp_dir)

def test_load_user_settings_with_unreadable_file(temp_config_file, monkeypatch):
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    os.chmod(temp_config_file, 0)
    try:
        loaded_settings = load_user_settings()
        assert loaded_settings == DEFAULT_SETTINGS
    finally:
        os.chmod(temp_config_file, 0o666)
        os.remove(temp_config_file)

def test_load_user_settings_when_config_file_is_directory(temp_config_directory, monkeypatch):
    if sys.platform == 'win32':
        with pytest.raises(PermissionError):
            load_user_settings()
    else:
        with pytest.raises(IsADirectoryError):
            load_user_settings()

def test_load_user_settings_with_additional_unknown_keys(temp_config_file, monkeypatch):
    settings_with_extra_keys = {
        'output': 'custom_.map',
        'unknown_key': 'some_value',
        'another_unknown': 123
    }
    save_user_settings(settings_with_extra_keys)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(settings_with_extra_keys)
    assert loaded_settings == expected_settings

def test_reset_settings_when_no_config_file_exists(temp_config_file, monkeypatch):
    monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', 'nonexistent_config.json')
    reset_settings()
    assert not os.path.exists('nonexistent_config.json')

def test_load_user_settings_with_empty_file(temp_config_file, monkeypatch):
    with open(temp_config_file, 'w') as f:
        pass
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_load_user_settings_with_null_values(temp_config_file, monkeypatch):
    settings_with_nulls = {
        'output': None,
        'ignore_hidden': None
    }
    save_user_settings(settings_with_nulls)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(settings_with_nulls)
    assert loaded_settings == expected_settings
    assert loaded_settings == expected_settings

def test_save_user_settings_creates_directory_if_not_exists(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    config_file = os.path.join(temp_dir, 'nonexistent_dir', 'config.json')
    monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', config_file)
    settings = {
        'output': 'custom_.map'
    }
    with pytest.raises(FileNotFoundError):
        save_user_settings(settings)
    assert not os.path.exists(os.path.join(temp_dir, 'nonexistent_dir'))
    shutil.rmtree(temp_dir)

def test_save_user_settings_handles_os_error(temp_config_file, monkeypatch):
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    os.chmod(temp_config_file, 0)
    settings = {
        'output': 'custom_.map'
    }
    try:
        with pytest.raises(OSError):
            save_user_settings(settings)
    finally:
        os.chmod(temp_config_file, 0o666)
        os.remove(temp_config_file)

def test_load_user_settings_with_symlinked_config_file(monkeypatch):
    if os.name == 'nt':
        pytest.skip("Symlinks are not supported or require administrative privileges on Windows.")
    with tempfile.TemporaryDirectory() as tmpdir:
        real_config_file = os.path.join(tmpdir, 'real_config.json')
        with open(real_config_file, 'w') as f:
            f.write(json.dumps({'output': 'real_.map'}))
        symlink_config_file = os.path.join(tmpdir, 'symlink_config.json')
        os.symlink(real_config_file, symlink_config_file)
        monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', symlink_config_file)
        loaded_settings = load_user_settings()
        assert loaded_settings == {
            'output': 'real_.map',
            'ignore': '.mapignore',
            'header': '.mapheader',
            'footer': '.mapfooter',
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }

def test_save_user_settings_with_relative_path(monkeypatch):
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir:
        config_file = os.path.join(tmpdir, 'config.json')
        relative_config_file = os.path.relpath(config_file)
        monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', relative_config_file)
        settings = {
            'output': 'custom_.map'
        }
        save_user_settings(settings)
        assert os.path.exists(config_file)
        with open(config_file, 'r') as f:
            data = json.load(f)
        assert data == settings

def test_load_user_settings_with_environment_variable_in_path(monkeypatch):
    with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir:
        config_file = os.path.join(tmpdir, 'config.json')
        env_var = 'TEST_CONFIG_PATH'
        os.environ[env_var] = config_file
        monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', os.path.expandvars(f'${env_var}'))
        settings = {
            'output': 'custom_.map'
        }
        save_user_settings(settings)
        loaded_settings = load_user_settings()
        expected_settings = DEFAULT_SETTINGS.copy()
        expected_settings.update(settings)
        assert loaded_settings == expected_settings
