import pytest
import os
import tempfile
import textwrap
from unittest.mock import patch, MagicMock
from mapper.core import generate_structure, reset_settings, get_version, traverse_directory, load_patterns
from pathspec import PathSpec

def test_generate_structure_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': os.path.join(tmpdir, '.mapignore'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }
        # Create empty PathSpec objects
        empty_spec = PathSpec.from_lines('gitwildmatch', [])
        with patch('mapper.core.load_patterns', return_value=(empty_spec, empty_spec)):
            generate_structure(settings, root=tmpdir)
            assert os.path.exists(settings['output'])
            with open(settings['output'], 'r') as f:
                content = f.read()
            assert content.strip() == ''

def test_traverse_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample directory structure
        os.makedirs(os.path.join(tmpdir, 'src'))
        with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
            f.write("# main.py")
        with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
            f.write("# README")
        
        patterns = (PathSpec.from_lines('gitwildmatch', []), PathSpec.from_lines('gitwildmatch', []))  # No ignore or omit patterns
        structure = traverse_directory(tmpdir, patterns, ignore_hidden=True)
        expected_structure = {
            'src': {
                'main.py': '# main.py'
            },
            'README.md': '# README'
        }
        assert structure == expected_structure

def test_apply_patterns():
    patterns_ignore = PathSpec.from_lines('gitwildmatch', ['*.md'])
    patterns_omit = PathSpec.from_lines('gitwildmatch', ['src/secret.py'])
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'src'))
        with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
            f.write("# main.py")
        with open(os.path.join(tmpdir, 'src', 'secret.py'), 'w') as f:
            f.write("# secret.py")
        with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
            f.write("# README")
        
        structure = traverse_directory(tmpdir, (patterns_ignore, patterns_omit), ignore_hidden=True)
        expected_structure = {
            'src': {
                'main.py': '# main.py',
                'secret.py': '[Content Omitted]'
            }
        }
        assert structure == expected_structure

def test_load_patterns():
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

def test_generate_structure_with_patterns():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup directory structure
        os.makedirs(os.path.join(tmpdir, 'src'))
        os.makedirs(os.path.join(tmpdir, 'config'))
        with open(os.path.join(tmpdir, 'src', 'main.py'), 'w', encoding='utf-8') as f:
            f.write("# main.py")
        with open(os.path.join(tmpdir, 'src', 'helper.pyc'), 'w', encoding='utf-8') as f:
            f.write("# helper.pyc")
        with open(os.path.join(tmpdir, 'config', 'settings.conf'), 'w', encoding='utf-8') as f:
            f.write("setting=value")
        with open(os.path.join(tmpdir, 'secret.txt'), 'w', encoding='utf-8') as f:
            f.write("Top Secret")

        # Create .mapignore and .mapomit
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w', encoding='utf-8') as f:
            f.write('*.pyc\nconfig/\nsecret.txt\n')
        with open(omit_path, 'w', encoding='utf-8') as f:
            f.write('')  # Ensure .mapomit is empty

        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': ignore_path,
            'header': None,
            'footer': None,
            'indent_char': '  ',  # Two spaces
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }

        generate_structure(settings, root=tmpdir)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()

        # Define the expected content with correct indentation using dedent
        expected_content = textwrap.dedent("""\
            Project Repository Structure:

            -> src
                -> main.py
            -> README.md

            ---

            README.md:

            ```
            # README
            ```

            ---
            src{}main.py:

            ```
            # main.py
            ```

            ---
            """.format(os.sep))

        # Debugging: Print actual and expected content
        print("Actual Content:")
        print(repr(content))
        print("Expected Content:")
        print(repr(expected_content))

        # Compare after stripping leading/trailing whitespace
        assert content.strip() == expected_content.strip()
