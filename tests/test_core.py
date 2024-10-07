import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from mapper.core import generate_structure, reset_settings, get_version, traverse_directory, load_patterns

def test_generate_structure_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': '.mapignore',
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }
        # Mock load_patterns to return empty patterns
        with patch('mapper.core.load_patterns', return_value=([], [])):
            generate_structure(settings)
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
        
        patterns = ([], [])  # No ignore or omit patterns
        structure = traverse_directory(tmpdir, patterns, ignore_hidden=True)
        expected_structure = {
            'src': {
                'main.py': '# main.py'
            },
            'README.md': '# README'
        }
        assert structure == expected_structure

def test_apply_patterns():
    patterns_ignore = ['*.md']
    patterns_omit = ['src/secret.py']
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
        
        ignore_patterns, omit_patterns = load_patterns(ignore_path, omit_path)
        assert ignore_patterns == ['*.pyc', '__pycache__/']
        assert omit_patterns == ['secret.txt', 'config/']

def test_generate_structure_with_patterns():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup directory structure
        os.makedirs(os.path.join(tmpdir, 'src'))
        os.makedirs(os.path.join(tmpdir, 'config'))
        with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
            f.write("# main.py")
        with open(os.path.join(tmpdir, 'src', 'helper.pyc'), 'w') as f:
            f.write("# helper.pyc")
        with open(os.path.join(tmpdir, 'config', 'settings.conf'), 'w') as f:
            f.write("setting=value")
        with open(os.path.join(tmpdir, 'secret.txt'), 'w') as f:
            f.write("Top Secret")
        
        # Create .mapignore and .mapomit
        ignore_path = os.path.join(tmpdir, '.mapignore')
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(ignore_path, 'w') as f:
            f.write('*.pyc\nconfig/\n')
        with open(omit_path, 'w') as f:
            f.write('secret.txt\n')
        
        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': ignore_path,
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }
        
        generate_structure(settings)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r') as f:
            content = f.read()
        expected_content = """src
    main.py
  """
        assert content.strip() == expected_content
