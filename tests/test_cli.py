import pytest
from click.testing import CliRunner
from mapper.cli import main

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Mapper version' in result.output

def test_generate_default():
    runner = CliRunner()
    result = runner.invoke(main, ['generate'])
    assert result.exit_code == 0
    assert 'Project structure generated' in result.output

def test_generate_with_custom_output():
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--output', 'custom_map.md'])
    assert result.exit_code == 0
    assert 'Project structure generated' in result.output

def test_reset_settings():
    runner = CliRunner()
    result = runner.invoke(main, ['reset-settings'])
    assert result.exit_code == 0
    assert 'Settings have been reset to default values.' in result.output

def test_generate_with_ignore_hidden():
    runner = CliRunner()
    result = runner.invoke(main, ['generate', '--ignore-hidden', 'false'])
    assert result.exit_code == 0
    assert 'Project structure generated' in result.output

def test_invalid_subcommand():
    runner = CliRunner()
    result = runner.invoke(main, ['invalid'])
    assert result.exit_code != 0
    assert 'No such command' in result.output
