import pytest
import os
import tempfile
from mapper.utils.file_utils import read_file_content
import sys

def test_read_file_content_small_file():
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write("Hello, World!")
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=100)
        assert result == "Hello, World!"
    finally:
        os.remove(temp_path)

def test_read_file_content_large_file():
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write('a' * 2000)
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=1000)
        assert result == 'a' * 1000 + '... [Truncated]'
    finally:
        os.remove(temp_path)

def test_read_file_content_exact_max_size():
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write('a' * 1000)
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=1000)
        assert result == 'a' * 1000
    finally:
        os.remove(temp_path)

def test_read_file_content_exactly_max_size_plus_one():
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write('a' * 1001)
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=1000)
        assert result == 'a' * 1000 + '... [Truncated]'
    finally:
        os.remove(temp_path)

def test_read_file_content_non_utf8_file():
    with tempfile.NamedTemporaryFile('wb', delete=False) as tf:
        tf.write(b'\xff\xfe\x00\x00')
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=100)
        assert result == '[Content Unreadable]'
    finally:
        os.remove(temp_path)

def test_read_file_content_nonexistent_file():
    temp_path = 'nonexistent.txt'
    result = read_file_content(temp_path, max_size=100)
    assert result == '[Content Unreadable]'

def test_read_file_content_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = read_file_content(tmpdir, max_size=100)
        assert result == '[Content Unreadable]'

def test_read_file_content_permission_error():
    if sys.platform == 'win32':
        pytest.skip("Skipping test on Windows due to OS limitations")
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.write("Restricted content")
        temp_path = tf.name
    os.chmod(temp_path, 0)
    try:
        result = read_file_content(temp_path, max_size=100)
        assert result == '[Content Unreadable]'
    finally:
        os.chmod(temp_path, 0o666)
        os.remove(temp_path)

def test_read_file_content_different_encoding():
    with tempfile.NamedTemporaryFile('w', encoding='latin-1', delete=False) as tf:
        tf.write("Café")
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=100)
        assert result == '[Content Unreadable]'
    finally:
        os.remove(temp_path)

def test_read_file_content_with_bom():
    with tempfile.NamedTemporaryFile('w', encoding='utf-8-sig', delete=False) as tf:
        tf.write("Hello, World!")
        temp_path = tf.name
    try:
        result = read_file_content(temp_path, max_size=100)
        assert result == "Hello, World!"
    finally:
        os.remove(temp_path)
