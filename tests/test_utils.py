import pytest
import os
import tempfile
from mapper.utils import (
    load_patterns, read_file_content, is_hidden, normalize_path
)

def test_normalize_path():
    # Test Windows-style paths
    assert normalize_path('folder\\subfolder\\file.txt') == 'folder/subfolder/file.txt'
    # Test Unix-style paths
    assert normalize_path('folder/subfolder/file.txt') == 'folder/subfolder/file.txt'
    # Test mixed paths
    assert normalize_path('folder\\subfolder/file.txt') == 'folder/subfolder/file.txt'
    # Test empty path
    assert normalize_path('') == ''
    # Test path with special characters
    assert normalize_path('folder\\subfolder\\spécial_文件.txt') == 'folder/subfolder/spécial_文件.txt'
    # Test path with multiple separators
    if os.name == 'nt':
        assert normalize_path('folder\\\\subfolder\\\\file.txt') == 'folder//subfolder//file.txt'
    else:
        assert normalize_path('folder//subfolder//file.txt') == 'folder//subfolder//file.txt'

def test_normalize_path_mixed_separators():
    path = os.path.join('folder', 'subfolder', 'file.txt')
    expected = 'folder/subfolder/file.txt'
    assert normalize_path(path) == expected

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
        # Invalid patterns (e.g., unmatched brackets)
        with open(ignore_path, 'w') as f:
            f.write('[*.txt\n')
        with open(omit_path, 'w') as f:
            f.write('**/[')
        # Since pathspec does not raise exceptions on invalid patterns, but may not match correctly
        ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
        # These patterns likely won't match anything
        assert ignore_spec.match_file('file.txt') is False
        assert omit_spec.match_file('dir/file') is False

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

def test_read_file_content_exact_max_size():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'test.txt')
        content = 'a' * 1000
        with open(file_path, 'w') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=1000)
        assert result == content

def test_read_file_content_exactly_max_size_plus_one():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'test.txt')
        content = 'a' * 1001
        with open(file_path, 'w') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=1000)
        assert result == 'a' * 1000 + '... [Truncated]'

def test_read_file_content_non_utf8_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'binary_file')
        # Write binary content
        with open(file_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')
        result = read_file_content(file_path, max_size=100)
        assert result == '[Content Unreadable]'

def test_read_file_content_nonexistent_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'nonexistent.txt')
        result = read_file_content(file_path, max_size=100)
        assert result == '[Content Unreadable]'

def test_read_file_content_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = read_file_content(tmpdir, max_size=100)
        assert result == '[Content Unreadable]'

def test_read_file_content_permission_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'restricted.txt')
        with open(file_path, 'w') as f:
            f.write('Restricted content')
        os.chmod(file_path, 0)  # Remove all permissions
        try:
            result = read_file_content(file_path, max_size=100)
            assert result == '[Content Unreadable]'
        finally:
            os.chmod(file_path, 0o666)

def test_read_file_content_different_encoding():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'test_latin1.txt')
        content = 'Café'  # Contains é character
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=100)
        # Since we open with 'utf-8', reading a 'latin-1' encoded file may cause UnicodeDecodeError
        assert result == '[Content Unreadable]'

def test_read_file_content_with_bom():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, 'test_bom.txt')
        content = 'Hello, World!'
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        result = read_file_content(file_path, max_size=100)
        assert result == content

def test_is_hidden_true():
    assert is_hidden('.gitignore') is True
    assert is_hidden('.env') is True

def test_is_hidden_false():
    assert is_hidden('main.py') is False
    assert is_hidden('README.md') is False

def test_is_hidden_nested():
    assert is_hidden('folder/.hidden/file.txt') is True
    assert is_hidden('folder/.hiddenfolder/file.txt') is True
    assert is_hidden('.hiddenfolder/subfolder/file.txt') is True
    assert is_hidden('folder/subfolder/file.txt') is False

def test_is_hidden_current_directory():
    assert is_hidden('./.hiddenfile') is True
    assert is_hidden('./file.txt') is False

def test_is_hidden_absolute_path():
    hidden_path = os.path.join(os.sep, 'home', 'user', '.hidden', 'file.txt')
    visible_path = os.path.join(os.sep, 'home', 'user', 'visible', 'file.txt')
    assert is_hidden(hidden_path) is True
    assert is_hidden(visible_path) is False

def test_is_hidden_empty_string():
    assert is_hidden('') is False

def test_is_hidden_single_dot():
    assert is_hidden('.') is True

def test_is_hidden_double_dot():
    assert is_hidden('..') is True

def test_is_hidden_root_directory():
    if os.name == 'nt':
        # On Windows
        assert is_hidden('C:\\') is False
    else:
        assert is_hidden('/') is False

def test_is_hidden_special_characters():
    assert is_hidden('folder/._file') is False  # Files starting with '._' are not hidden unless they start with '.'
    assert is_hidden('folder/.DS_Store') is True
    assert is_hidden('folder/.git/config') is True
