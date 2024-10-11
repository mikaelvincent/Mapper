import pytest
from click.testing import CliRunner
from mapper.cli import main
import os
import tempfile

@pytest.fixture
def temp_config_file(monkeypatch):
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        config_file = tf.name
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Mapper version' in result.output

def test_generate_default(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure '.map' is created
        assert os.path.exists('.map')

def test_generate_with_custom_output(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'custom_.map'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure 'custom_.map' is created
        assert os.path.exists('custom_.map')

def test_reset_settings(temp_config_file):
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

def test_generate_with_ignore_hidden(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--ignore-hidden', 'false'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure '.map' is created
        assert os.path.exists('.map')

def test_invalid_subcommand():
    runner = CliRunner()
    result = runner.invoke(main, ['invalid'])
    assert result.exit_code != 0
    assert 'No such command' in result.output
