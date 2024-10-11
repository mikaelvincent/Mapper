import pytest
import os
import tempfile
import json
from mapper.config import save_user_settings, load_user_settings, reset_settings, DEFAULT_SETTINGS, CONFIG_FILE
from unittest.mock import patch
import shutil

@pytest.fixture
def temp_config_file():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()  # Ensure the file is closed before yielding
    yield tf.name
    if os.path.exists(tf.name):
        if os.path.isfile(tf.name):
            os.remove(tf.name)
        else:
            shutil.rmtree(tf.name)

def test_default_settings():
    """Test that DEFAULT_SETTINGS contains the expected default values."""
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
    """Test that save_user_settings correctly saves settings to the config file."""
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
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = f.read()
    assert '"output": "custom_.map"' in loaded_settings
    assert '"ignore_hidden": false' in loaded_settings
    assert '"indent_char": "  "' in loaded_settings
    assert '"arrow": "-->"' in loaded_settings

def test_load_user_settings(temp_config_file, monkeypatch):
    """Test that load_user_settings correctly loads settings from the config file."""
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
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    loaded_settings = load_user_settings()
    assert loaded_settings == settings

def test_load_user_settings_default(temp_config_file, monkeypatch):
    """Test that load_user_settings returns DEFAULT_SETTINGS when config file doesn't exist."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    # Ensure the config file does not exist
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_save_user_settings_with_missing_keys(temp_config_file, monkeypatch):
    """Test saving settings when some keys are missing."""
    settings = {
        'output': 'custom_.map'
        # Missing other keys
    }
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = json.load(f)
    assert loaded_settings == settings  # Should only contain 'output' key

def test_load_user_settings_with_partial_settings(temp_config_file, monkeypatch):
    """Test loading settings when the config file has partial settings."""
    partial_settings = {
        'output': 'custom_.map',
        'verbose': True
    }
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with open(temp_config_file, 'w') as f:
        json.dump(partial_settings, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(partial_settings)
    assert loaded_settings == expected_settings

def test_load_user_settings_with_invalid_json(temp_config_file, monkeypatch):
    """Test that load_user_settings returns DEFAULT_SETTINGS when config file has invalid JSON."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with open(temp_config_file, 'w') as f:
        f.write('invalid json')
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_reset_settings_removes_config_file(temp_config_file, monkeypatch):
    """Test that reset_settings removes the config file."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    assert os.path.exists(temp_config_file)
    reset_settings()
    assert not os.path.exists(temp_config_file)

def test_save_user_settings_overwrites_existing_file(temp_config_file, monkeypatch):
    """Test that save_user_settings overwrites existing config file."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    initial_settings = {
        'output': 'initial_.map'
    }
    updated_settings = {
        'output': 'updated_.map'
    }
    save_user_settings(initial_settings)
    with open(temp_config_file, 'r') as f:
        data = json.load(f)
    assert data == initial_settings
    save_user_settings(updated_settings)
    with open(temp_config_file, 'r') as f:
        data = json.load(f)
    assert data == updated_settings

def test_save_user_settings_with_invalid_data(temp_config_file, monkeypatch):
    """Test that save_user_settings raises TypeError when settings contain non-serializable data."""
    settings = {
        'output': 'custom_.map',
        'invalid_key': set([1, 2, 3])  # Sets are not JSON serializable
    }
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with pytest.raises(TypeError):
        save_user_settings(settings)

def test_load_user_settings_with_incorrect_data_types(temp_config_file, monkeypatch):
    """Test that load_user_settings loads settings even when data types are incorrect."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    incorrect_settings = {
        'output': 123,  # Should be a string
        'ignore_hidden': 'yes'  # Should be a boolean
    }
    with open(temp_config_file, 'w') as f:
        json.dump(incorrect_settings, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(incorrect_settings)
    assert loaded_settings == expected_settings

def test_save_user_settings_with_nonexistent_directory(monkeypatch):
    """Test that save_user_settings raises FileNotFoundError when directory does not exist."""
    temp_dir = tempfile.mkdtemp()
    non_existent_dir = os.path.join(temp_dir, 'nonexistent')
    config_file = os.path.join(non_existent_dir, 'config.json')
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    settings = {
        'output': 'custom_.map'
    }
    with pytest.raises(FileNotFoundError):
        save_user_settings(settings)
    # Clean up
    os.rmdir(temp_dir)

def test_load_user_settings_with_unreadable_file(temp_config_file, monkeypatch):
    """Test that load_user_settings returns DEFAULT_SETTINGS when the config file is unreadable."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    os.chmod(temp_config_file, 0)  # Remove all permissions to make the file unreadable
    try:
        loaded_settings = load_user_settings()
        assert loaded_settings == DEFAULT_SETTINGS, "Should return DEFAULT_SETTINGS when config file is unreadable."
    finally:
        os.chmod(temp_config_file, 0o666)  # Restore permissions for cleanup
        os.remove(temp_config_file)

def test_load_user_settings_when_config_file_is_directory(temp_config_file, monkeypatch):
    """Test that load_user_settings raises the appropriate error when config file is a directory."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    os.remove(temp_config_file)
    os.makedirs(temp_config_file)
    try:
        if os.name == 'nt':
            expected_exception = PermissionError
        else:
            expected_exception = IsADirectoryError
        with pytest.raises(expected_exception):
            load_user_settings()
    finally:
        shutil.rmtree(temp_config_file)

def test_load_user_settings_with_additional_unknown_keys(temp_config_file, monkeypatch):
    """Test that load_user_settings includes unknown keys in the config file."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    settings_with_extra_keys = {
        'output': 'custom_.map',
        'unknown_key': 'some_value',
        'another_unknown': 123
    }
    with open(temp_config_file, 'w') as f:
        json.dump(settings_with_extra_keys, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(settings_with_extra_keys)
    assert loaded_settings == expected_settings

def test_reset_settings_when_no_config_file_exists(temp_config_file, monkeypatch):
    """Test that reset_settings does not raise an error when config file doesn't exist."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    # Ensure the config file does not exist
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)
    # Should not raise any exception
    reset_settings()
    assert not os.path.exists(temp_config_file)

def test_load_user_settings_with_empty_file(temp_config_file, monkeypatch):
    """Test that load_user_settings returns DEFAULT_SETTINGS when config file is empty."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    # Create an empty config file
    with open(temp_config_file, 'w') as f:
        pass
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

def test_load_user_settings_with_null_values(temp_config_file, monkeypatch):
    """Test that load_user_settings handles null values in the config file."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    settings_with_nulls = {
        'output': None,
        'ignore_hidden': None
    }
    with open(temp_config_file, 'w') as f:
        json.dump(settings_with_nulls, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update({'output': None, 'ignore_hidden': None})
    assert loaded_settings == expected_settings

def test_save_user_settings_creates_directory_if_not_exists(temp_config_file, monkeypatch):
    """Test that save_user_settings raises an error if the directory does not exist."""
    config_dir = os.path.dirname(temp_config_file)
    non_existent_dir = os.path.join(config_dir, 'nonexistent_dir')
    config_file = os.path.join(non_existent_dir, 'config.json')
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    settings = {
        'output': 'custom_.map'
    }
    with pytest.raises(FileNotFoundError):
        save_user_settings(settings)
    assert not os.path.exists(non_existent_dir)

def test_save_user_settings_handles_os_error(temp_config_file, monkeypatch):
    """Test that save_user_settings raises OSError when unable to write to config file."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    with open(temp_config_file, 'w') as f:
        f.write('{}')
    os.chmod(temp_config_file, 0)  # Make the file unwritable
    settings = {
        'output': 'custom_.map'
    }
    try:
        with pytest.raises(OSError):
            save_user_settings(settings)
    finally:
        os.chmod(temp_config_file, 0o666)
        os.remove(temp_config_file)

def test_load_user_settings_with_symlinked_config_file(temp_config_file, monkeypatch):
    """Test that load_user_settings works when config file is a symlink."""
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    real_config_file = temp_config_file + '_real'
    os.rename(temp_config_file, real_config_file)
    try:
        os.symlink(real_config_file, temp_config_file)
    except (OSError, NotImplementedError, AttributeError) as e:
        pytest.skip("Symlinks not supported or insufficient privileges on this platform.")
    settings = {
        'output': 'custom_.map'
    }
    with open(real_config_file, 'w') as f:
        json.dump(settings, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(settings)
    assert loaded_settings == expected_settings
    # Clean up
    os.remove(temp_config_file)
    os.remove(real_config_file)

def test_save_user_settings_with_relative_path(monkeypatch):
    """Test that save_user_settings works with relative CONFIG_FILE path."""
    temp_dir = tempfile.mkdtemp()
    config_file = os.path.join(temp_dir, 'config.json')
    cwd_drive = os.path.splitdrive(os.getcwd())[0]
    temp_drive = os.path.splitdrive(temp_dir)[0]
    if cwd_drive.lower() != temp_drive.lower():
        pytest.skip("Cannot compute relative path across different drives.")
    relative_config_file = os.path.relpath(config_file)
    monkeypatch.setattr('mapper.config.CONFIG_FILE', relative_config_file)
    settings = {
        'output': 'custom_.map'
    }
    save_user_settings(settings)
    assert os.path.exists(config_file)
    with open(config_file, 'r') as f:
        data = json.load(f)
    assert data == settings
    # Clean up
    os.remove(config_file)
    os.rmdir(temp_dir)

def test_load_user_settings_with_environment_variable_in_path(monkeypatch):
    """Test that load_user_settings expands environment variables in CONFIG_FILE path."""
    temp_dir = tempfile.mkdtemp()
    config_file = os.path.join(temp_dir, 'config.json')
    env_var = 'TEST_CONFIG_PATH'
    os.environ[env_var] = config_file
    monkeypatch.setattr('mapper.config.CONFIG_FILE', os.path.expandvars(f'${env_var}'))
    settings = {
        'output': 'custom_.map'
    }
    with open(config_file, 'w') as f:
        json.dump(settings, f)
    loaded_settings = load_user_settings()
    expected_settings = DEFAULT_SETTINGS.copy()
    expected_settings.update(settings)
    assert loaded_settings == expected_settings
    # Clean up
    os.remove(config_file)
    os.rmdir(temp_dir)
    del os.environ[env_var]
