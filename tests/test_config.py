import pytest
import os
import tempfile
from config import save_user_settings, load_user_settings, DEFAULT_SETTINGS

@pytest.fixture
def temp_config_file():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        yield tf.name
    os.remove(tf.name)

def test_default_settings():
    assert DEFAULT_SETTINGS == {
        'output': 'map.md',
        'ignore': '.mapignore',
        'header': '.mapheader',
        'footer': '.mapfooter',
        'indent_char': '  ',
        'arrow': '-->',
        'ignore_hidden': True,
        'max_size': 1000000,
        'verbose': False,
        'quiet': False
    }

def test_save_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_map.md',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': False
    }
    monkeypatch.setattr('config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = f.read()
    assert '"output": "custom_map.md"' in loaded_settings
    assert '"ignore_hidden": false' in loaded_settings

def test_load_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_map.md',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': False
    }
    monkeypatch.setattr('config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    loaded_settings = load_user_settings()
    assert loaded_settings == settings

def test_load_user_settings_default(temp_config_file, monkeypatch):
    monkeypatch.setattr('config.CONFIG_FILE', temp_config_file)
    # Ensure the config file does not exist
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS
