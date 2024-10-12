import pytest
import os
import tempfile
import re
from unittest.mock import patch, MagicMock
from mapper.core import (
    generate_structure, reset_settings, get_version, traverse_directory,
    load_patterns, generate_markdown, strip_empty_lines
)
from mapper.utils import normalize_path
from pathspec import PathSpec

def test_get_version():
    version = get_version()
    assert version == '0.1.0'

def test_reset_settings():
    with patch('mapper.core.reset_settings') as mock_reset:
        reset_settings()
        mock_reset.assert_called_once()

def test_strip_empty_lines():
    text = "\n\n   \nLine1\nLine2\n\n   \n"
    expected = "Line1\nLine2"
    result = strip_empty_lines(text)
    assert result == expected

def test_traverse_directory_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_spec = PathSpec.from_lines('gitwildmatch', [])
        omit_spec = PathSpec.from_lines('gitwildmatch', [])
        structure, file_contents = traverse_directory(tmpdir, (ignore_spec, omit_spec), ignore_hidden=True)
        assert structure == {}
        assert file_contents == {}

def test_traverse_directory_with_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'dir'))
        with open(os.path.join(tmpdir, 'dir', 'file.txt'), 'w') as f:
            f.write('content')
        ignore_spec = PathSpec.from_lines('gitwildmatch', [])
        omit_spec = PathSpec.from_lines('gitwildmatch', [])
        structure, file_contents = traverse_directory(tmpdir, (ignore_spec, omit_spec), ignore_hidden=True)
        assert 'dir' in structure
        assert 'file.txt' in structure['dir']
        assert file_contents['dir/file.txt'] == 'content'

def test_traverse_directory_with_ignore():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'ignore_dir'))
        with open(os.path.join(tmpdir, 'ignore_dir', 'file.txt'), 'w') as f:
            f.write('should be ignored')
        os.makedirs(os.path.join(tmpdir, 'include_dir'))
        with open(os.path.join(tmpdir, 'include_dir', 'file.txt'), 'w') as f:
            f.write('should be included')
        ignore_spec = PathSpec.from_lines('gitwildmatch', ['ignore_dir/'])
        omit_spec = PathSpec.from_lines('gitwildmatch', [])
        structure, file_contents = traverse_directory(tmpdir, (ignore_spec, omit_spec), ignore_hidden=True)
        assert 'ignore_dir' not in structure
        assert 'include_dir' in structure
        assert 'file.txt' in structure['include_dir']
        assert 'include_dir/file.txt' in file_contents
        assert file_contents['include_dir/file.txt'] == 'should be included'

def test_traverse_directory_with_omit():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'omit_dir'))
        with open(os.path.join(tmpdir, 'omit_dir', 'file.txt'), 'w') as f:
            f.write('should be omitted')
        os.makedirs(os.path.join(tmpdir, 'include_dir'))
        with open(os.path.join(tmpdir, 'include_dir', 'file.txt'), 'w') as f:
            f.write('should be included')
        ignore_spec = PathSpec.from_lines('gitwildmatch', [])
        omit_spec = PathSpec.from_lines('gitwildmatch', ['omit_dir/'])
        structure, file_contents = traverse_directory(tmpdir, (ignore_spec, omit_spec), ignore_hidden=True)
        assert 'omit_dir' in structure
        assert structure['omit_dir'] == {'[omitted]': None}
        assert 'include_dir' in structure
        assert 'file.txt' in structure['include_dir']
        assert 'include_dir/file.txt' in file_contents
        assert file_contents['include_dir/file.txt'] == 'should be included'
        assert file_contents['omit_dir/file.txt'] == '[omitted]'

def test_generate_markdown_no_files():
    structure = {'Folder': {}}
    file_contents = {}
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    markdown = generate_markdown(structure, file_contents, settings)
    expected = "Project Repository Structure:\n\n-> Folder\n"
    assert markdown.strip() == expected.strip()

def test_generate_markdown_with_files():
    structure = {
        'Folder': {
            'Subfolder': {
                'file.txt': None
            }
        }
    }
    file_contents = {
        'Folder/Subfolder/file.txt': 'content'
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    markdown = generate_markdown(structure, file_contents, settings)
    assert '-> Folder' in markdown
    assert '-> Subfolder' in markdown
    assert '-> file.txt' in markdown
    assert 'Folder/Subfolder/file.txt:' in markdown
    assert 'content' in markdown

def test_generate_markdown_with_truncated_content():
    structure = {
        'Folder': {
            'file.txt': None
        }
    }
    file_contents = {
        'Folder/file.txt': 'a' * 1001
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    markdown = generate_markdown(structure, file_contents, settings)
    assert '... [Truncated]' in markdown

def test_generate_markdown_with_header_footer(tmpdir):
    header_path = os.path.join(tmpdir, 'header.txt')
    footer_path = os.path.join(tmpdir, 'footer.txt')
    with open(header_path, 'w') as f:
        f.write('Header Content\n\n')
    with open(footer_path, 'w') as f:
        f.write('Footer Content\n\n')
    structure = {
        'Folder': {
            'file.txt': None
        }
    }
    file_contents = {
        'Folder/file.txt': 'content'
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000,
        'header': header_path,
        'footer': footer_path
    }
    markdown = generate_markdown(structure, file_contents, settings)
    assert 'Header Content' in markdown
    assert 'Footer Content' in markdown
    assert '-> Folder' in markdown

def test_generate_markdown_with_omitted_files():
    structure = {
        'Folder': {
            'file.txt': None,
            'secret.txt': None
        }
    }
    file_contents = {
        'Folder/file.txt': 'content',
        'Folder/secret.txt': '[omitted]'
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    markdown = generate_markdown(structure, file_contents, settings)
    assert 'secret.txt' in markdown
    assert '[omitted]' in markdown

def test_generate_structure(tmpdir):
    os.makedirs(os.path.join(tmpdir, 'dir/subdir'))
    with open(os.path.join(tmpdir, 'dir/subdir/file.txt'), 'w') as f:
        f.write('content')
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert '-> dir' in content
        assert '-> subdir' in content
        assert '-> file.txt' in content
        assert 'file.txt:\n\n```
```' in content

def test_generate_structure_with_hidden_files(tmpdir):
    with open(os.path.join(tmpdir, '.hidden_file'), 'w') as f:
        f.write('hidden')
    with open(os.path.join(tmpdir, 'visible_file'), 'w') as f:
        f.write('visible')
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert 'visible_file' in content
        assert '.hidden_file' not in content

def test_generate_structure_with_symlinks(tmpdir):
    os.makedirs(os.path.join(tmpdir, 'dir'))
    with open(os.path.join(tmpdir, 'dir/file.txt'), 'w') as f:
        f.write('content')
    try:
        os.symlink('dir', os.path.join(tmpdir, 'link_to_dir'))
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("Symlinks not supported or insufficient privileges on this platform.")
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert 'link_to_dir' in content

def test_generate_structure_with_max_size(tmpdir):
    with open(os.path.join(tmpdir, 'large_file.txt'), 'w') as f:
        f.write('a' * 2000)
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert '... [Truncated]' in content

def test_generate_structure_with_header_footer(tmpdir):
    header_path = os.path.join(tmpdir, 'header.txt')
    footer_path = os.path.join(tmpdir, 'footer.txt')
    with open(header_path, 'w') as f:
        f.write('Header Content\n\n')
    with open(footer_path, 'w') as f:
        f.write('Footer Content\n\n')
    with open(os.path.join(tmpdir, 'file.txt'), 'w') as f:
        f.write('content')
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': header_path,
        'footer': footer_path,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert 'Header Content' in content
        assert 'Footer Content' in content
        assert '-> file.txt' in content

def test_generate_structure_with_permission_error(tmpdir):
    output_path = os.path.join(tmpdir, 'output.map')
    with open(output_path, 'w') as f:
        f.write('')
    os.chmod(output_path, 0o444)
    settings = {
        'output': output_path,
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '  ',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        with pytest.raises(PermissionError):
            generate_structure(settings, root=tmpdir)
    os.chmod(output_path, 0o666)

def test_generate_structure_with_different_indent_and_arrow(tmpdir):
    os.makedirs(os.path.join(tmpdir, 'dir'))
    with open(os.path.join(tmpdir, 'dir/file.txt'), 'w') as f:
        f.write('content')
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '--',
        'arrow': '=>',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        assert '--=> dir' in content
        assert '--=> file.txt' in content

def test_generate_structure_with_deeply_nested_directories(tmpdir):
    current_dir = tmpdir
    for i in range(10):
        next_dir = os.path.join(current_dir, f'dir_{i}')
        os.makedirs(next_dir)
        with open(os.path.join(next_dir, f'file_{i}.txt'), 'w') as f:
            f.write(f'Content {i}')
        current_dir = next_dir
    settings = {
        'output': os.path.join(tmpdir, 'output.map'),
        'ignore': '.mapignore',
        'omit': '.mapomit',
        'header': None,
        'footer': None,
        'indent_char': '    ',
        'arrow': '-->',
        'ignore_hidden': True,
        'max_size': 1000
    }
    ignore_spec = PathSpec.from_lines('gitwildmatch', [])
    omit_spec = PathSpec.from_lines('gitwildmatch', [])
    with patch('mapper.core.load_patterns', return_value=(ignore_spec, omit_spec)):
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r') as f:
            content = f.read()
        for i in range(10):
            assert f'dir_{i}' in content
            assert f'file_{i}.txt' in content
