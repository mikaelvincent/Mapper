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
    monkeypatch.setattr('mapper.config.settings.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

def test_reset_settings(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open(temp_config_file, 'w') as f:
            f.write('{}')
        result = runner.invoke(main, ['reset-settings'])
        assert result.exit_code == 0
        assert 'Settings have been reset to default values.' in result.output
        assert not os.path.exists(temp_config_file)
