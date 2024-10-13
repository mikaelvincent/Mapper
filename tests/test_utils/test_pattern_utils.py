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

def test_load_patterns_with_overlapping_ignore_and_omit():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('*.log\nconfig/\nshared/*.txt\n')
        with open(omit_path, 'w') as f:
            f.write('config/secret/\nshared/important.txt\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('debug.log') is True
        assert omit_spec.match_file('config/secret/') is True
        assert omit_spec.match_file('shared/important.txt') is True
        assert omit_spec.match_file('shared/other.txt') is False
        assert ignore_spec.match_file('shared/other.txt') is True
        assert omit_spec.match_file('config/settings.py') is False
        assert ignore_spec.match_file('config/settings.py') is True

def test_load_patterns_overlap_file_and_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('temp/\n*.tmp\n')
        with open(omit_path, 'w') as f:
            f.write('temp/cache/\nimportant.tmp\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert omit_spec.match_file('temp/cache/') is True
        assert omit_spec.match_file('temp/cache/data.tmp') is True

def test_load_patterns_overlap_same_pattern():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        pattern = '*.bak\n'
        with open(ignore_path, 'w') as f:
            f.write(pattern)
        with open(omit_path, 'w') as f:
            f.write(pattern)
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert omit_spec.match_file('backup.bak') is True
        assert ignore_spec.match_file('backup.bak') is True

def test_load_patterns_overlap_nested_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('logs/\nlogs/*.log\n')
        with open(omit_path, 'w') as f:
            f.write('logs/archive/\nlogs/archive/*.log\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert omit_spec.match_file('logs/archive/') is True
        assert omit_spec.match_file('logs/archive/old.log') is True
        assert ignore_spec.match_file('logs/archive/old.log') is True
        assert ignore_spec.match_file('logs/current.log') is True
        assert omit_spec.match_file('logs/current.log') is False

def test_load_patterns_no_overlap():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('*.tmp\nbuild/\n')
        with open(omit_path, 'w') as f:
            f.write('docs/secret/\n*.conf\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('temp.tmp') is True
        assert omit_spec.match_file('docs/secret/') is True
        assert omit_spec.match_file('config.conf') is True
        assert ignore_spec.match_file('docs/secret/config.conf') is False

def test_load_patterns_file_ignored_and_omitted():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('*.md\n')
        with open(omit_path, 'w') as f:
            f.write('README.md\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('README.md') is True
        assert omit_spec.match_file('README.md') is True

def test_load_patterns_directory_ignored_and_omitted():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('logs/\n')
        with open(omit_path, 'w') as f:
            f.write('logs/\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('logs/') is True
        assert omit_spec.match_file('logs/') is True

def test_load_patterns_file_omitted_directory_ignored():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('temp/\n')
        with open(omit_path, 'w') as f:
            f.write('temp/cache_file.txt\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert ignore_spec.match_file('temp/') is True
        assert omit_spec.match_file('temp/cache_file.txt') is True
        assert ignore_spec.match_file('temp/cache_file.txt') is True

def test_load_patterns_directory_omitted_file_ignored():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('config/\n')
        with open(omit_path, 'w') as f:
            f.write('config/settings.conf\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        assert omit_spec.match_file('config/settings.conf') is True
        assert ignore_spec.match_file('config/settings.conf') is True
        assert ignore_spec.match_file('config/') is True

def test_load_patterns_ignore_directory_exempt_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        with open(ignore_path, 'w') as f:
            f.write('logs/\n!logs/important.log\n')
        ignore_spec, omit_spec = load_patterns(ignore_path, '.mapomit')
        assert ignore_spec.match_file('logs/') is True
        assert ignore_spec.match_file('logs/important.log') is False
        assert ignore_spec.match_file('logs/other.log') is True

def test_load_patterns_omit_directory_exempt_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(omit_path, 'w') as f:
            f.write('secrets/\n!secrets/allowed.txt\n')
        ignore_spec, omit_spec = load_patterns('.mapignore', omit_path)
        assert omit_spec.match_file('secrets/') is True
        assert omit_spec.match_file('secrets/allowed.txt') is False
        assert omit_spec.match_file('secrets/hidden.txt') is True
