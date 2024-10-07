import pytest
import os
import tempfile
from mapper.utils import load_patterns, read_file_content, is_hidden

def test_load_patterns_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('')
        with open(omit_path, 'w') as f:
            f.write('')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('anyfile') is False
        assert omit_spec.match_file('anyfile') is False

def test_load_patterns_with_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('*.pyc\n__pycache__/\n')
        with open(omit_path, 'w') as f:
            f.write('secret.txt\nconfig/\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('module.pyc') is True
        assert ignore_spec.match_file('__pycache__/') is True
        assert omit_spec.match_file('secret.txt') is True
        assert omit_spec.match_file('config/') is True

def test_read_file_content_small_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'test.txt')
        content = 'Hello, World!'
        with open(file_path, 'w') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=100)
        assert result == content

def test_read_file_content_large_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'large.txt')
        content = 'a' * 2000
        with open(file_path, 'w') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=1000)
        assert result == 'a' * 1000 + '... [Truncated]'

def test_is_hidden_true():
    assert is_hidden('.gitignore') is True
    assert is_hidden('.env') is True

def test_is_hidden_false():
    assert is_hidden('main.py') is False
    assert is_hidden('README.md') is False
