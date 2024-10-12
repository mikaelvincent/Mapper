import pytest
from click.testing import CliRunner
from mapper.cli.main import main

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Mapper version' in result.output
