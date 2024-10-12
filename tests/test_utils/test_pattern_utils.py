import pytest
import os
import tempfile
from mapper.utils.pattern_utils import load_patterns
from pathspec import PathSpec

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

def test_load_patterns_with_comments_and_blank_lines():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('# This is a comment\n\n*.log\n')
        with open(omit_path, 'w') as f:
            f.write('\n# Omit patterns\nsecret/*\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('debug.log') is True
        assert omit_spec.match_file('secret/file.txt') is True

def test_load_patterns_with_leading_trailing_whitespace():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('  *.tmp  \n')
        with open(omit_path, 'w') as f:
            f.write('  cache/  \n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('file.tmp') is True
        assert omit_spec.match_file('cache/') is True

def test_load_patterns_with_special_characters():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w', encoding='utf-8') as f:
            f.write('spécial_文件.txt\n')
        with open(omit_path, 'w', encoding='utf-8') as f:
            f.write('特殊/*\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('spécial_文件.txt') is True
        assert omit_spec.match_file('特殊/file.txt') is True

def test_load_patterns_with_invalid_patterns():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('[*.txt\n')
        with open(omit_path, 'w') as f:
            f.write('**/[')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('file.txt') is False
        assert omit_spec.match_file('dir/file') is False
