import pytest
import os
from mapper.utils.path_utils import normalize_path, is_hidden

def test_normalize_path():
    assert normalize_path('folder\\subfolder\\file.txt') == 'folder/subfolder/file.txt'
    assert normalize_path('folder/subfolder/file.txt') == 'folder/subfolder/file.txt'
    assert normalize_path('folder\\subfolder/file.txt') == 'folder/subfolder/file.txt'
    assert normalize_path('') == ''
    assert normalize_path('folder\\subfolder\\spécial_文件.txt') == 'folder/subfolder/spécial_文件.txt'
    if os.name == 'nt':
        assert normalize_path('folder\\\\subfolder\\\\file.txt') == 'folder//subfolder//file.txt'
    else:
        assert normalize_path('folder//subfolder//file.txt') == 'folder//subfolder//file.txt'

def test_normalize_path_mixed_separators():
    path = os.path.join('folder', 'subfolder', 'file.txt')
    expected = 'folder/subfolder/file.txt'
    assert normalize_path(path) == expected

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
        assert is_hidden('C:\\') is False
    else:
        assert is_hidden('/') is False

def test_is_hidden_special_characters():
    assert is_hidden('folder/._file') is False
    assert is_hidden('folder/.DS_Store') is True
    assert is_hidden('folder/.git/config') is True
