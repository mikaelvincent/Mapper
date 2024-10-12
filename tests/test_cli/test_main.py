import pytest
from click.testing import CliRunner
from mapper.cli.main import main

def test_help_command():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output
    assert 'Commands:' in result.output

def test_invalid_subcommand():
    runner = CliRunner()
    result = runner.invoke(main, ['invalid'])
    assert result.exit_code != 0
    assert 'No such command' in result.output
