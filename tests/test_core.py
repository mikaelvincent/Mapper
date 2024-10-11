import pytest
import os
import tempfile
import textwrap
import re
from unittest.mock import patch, MagicMock
from mapper.core import (
    generate_structure, reset_settings, get_version, traverse_directory,
    load_patterns, generate_markdown, strip_empty_lines
)
from pathspec import PathSpec
from mapper.utils import normalize_path

def test_get_version():
    """Test that get_version returns the correct version."""
    version = get_version()
    assert version == '0.1.0'

def test_reset_settings():
    """Test that reset_settings function calls config_reset_settings."""
    with patch('mapper.core.config_reset_settings') as mock_reset:
        reset_settings()
        mock_reset.assert_called_once()

def test_strip_empty_lines():
    """Test strip_empty_lines function."""
    text = "\n\n   \nLine1\nLine2\n\n   \n"
    expected = "Line1\nLine2"
    result = strip_empty_lines(text)
    assert result == expected

def test_generate_structure_empty_directory():
    """Test generate_structure with an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
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
            with open(settings['output'], 'r', encoding='utf-8') as f:
                content = f.read()
        assert content.strip() == 'Project Repository Structure:'

def test_generate_structure_with_hidden_files():
    """Test generate_structure with hidden files and ignore_hidden setting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create hidden and non-hidden files
        with open(os.path.join(tmpdir, '.hidden_file.txt'), 'w', encoding='utf-8') as f:
            f.write("Hidden Content")
        with open(os.path.join(tmpdir, 'visible_file.txt'), 'w', encoding='utf-8') as f:
            f.write("Visible Content")
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,  # Hidden files should be ignored
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }
        # Create empty PathSpec objects
        empty_spec = PathSpec.from_lines('gitwildmatch', [])
        with patch('mapper.core.load_patterns', return_value=(empty_spec, empty_spec)):
            generate_structure(settings, root=tmpdir)
            assert os.path.exists(settings['output'])
            with open(settings['output'], 'r', encoding='utf-8') as f:
                content = f.read()
        assert 'visible_file.txt' in content
        assert '.hidden_file.txt' not in content

        # Now test with ignore_hidden=False
        settings['ignore_hidden'] = False
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'visible_file.txt' in content
        assert '.hidden_file.txt' in content

def test_generate_structure_with_special_characters():
    """Test generate_structure with files and directories containing special characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'spécial_目录'))
        with open(os.path.join(tmpdir, 'spécial_目录', '文件.txt'), 'w', encoding='utf-8') as f:
            f.write("Special Content")
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '    ',  # Four spaces
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'spécial_目录' in content
        assert '文件.txt' in content
        assert '-->' in content
        assert '    ' in content  # Indentation

def test_generate_structure_with_large_files():
    """Test generate_structure handles large files with max_size truncation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        large_content = 'a' * 2000
        file_path = os.path.join(tmpdir, 'large_file.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(large_content)
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,  # Set max_size to 1000 bytes
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        # Check that '... [Truncated]' is in the content
        assert '... [Truncated]' in content
        # Extract the content of the file from the markdown
        match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
        assert match is not None
        file_content = match.group(1)
        # Remove the '... [Truncated]' at the end
        truncated_content = file_content.replace('... [Truncated]', '').strip()
        # Count the number of 'a's
        assert len(truncated_content) == 1000

def test_generate_structure_with_non_utf8_files():
    """Test generate_structure handles files with non-UTF-8 encoding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a binary file
        with open(os.path.join(tmpdir, 'binary_file.bin'), 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert '[Content Unreadable]' in content

def test_generate_structure_with_symlinks():
    """Test generate_structure with symlinks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = os.path.join(tmpdir, 'target_dir')
        os.makedirs(target_dir)
        with open(os.path.join(target_dir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Target Content')
        symlink_dir = os.path.join(tmpdir, 'symlink_dir')
        try:
            os.symlink(target_dir, symlink_dir)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this platform")

        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        # Check that symlink is included
        assert 'symlink_dir' in content
        # Depending on os.walk's behavior, the symlink may or may not be traversed

def test_generate_structure_with_deeply_nested_directories():
    """Test generate_structure with deeply nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        current_dir = tmpdir
        for i in range(10):
            next_dir = os.path.join(current_dir, f'dir_{i}')
            os.makedirs(next_dir)
            with open(os.path.join(next_dir, f'file_{i}.txt'), 'w', encoding='utf-8') as f:
                f.write(f'Content {i}')
            current_dir = next_dir
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '    ',  # Four spaces
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        # Check that all directories and files are included
        for i in range(10):
            assert f'dir_{i}' in content
            assert f'file_{i}.txt' in content

def test_generate_structure_with_invalid_output_path():
    """Test generate_structure when output path is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_output_path = os.path.join(tmpdir, 'nonexistent_dir', '.map')
        settings = {
            'output': invalid_output_path,
            'header': None,
            'footer': None,
            'indent_char': '    ',
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        with pytest.raises(FileNotFoundError):
            generate_structure(settings, root=tmpdir)

def test_generate_structure_with_permission_error():
    """Test generate_structure when output file cannot be written due to permission error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, '.map')
        # Create the output file and make it unwritable
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('')
        os.chmod(output_path, 0o444)  # Read-only
        settings = {
            'output': output_path,
            'header': None,
            'footer': None,
            'indent_char': '    ',
            'arrow': '-->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        try:
            with pytest.raises(PermissionError):
                generate_structure(settings, root=tmpdir)
        finally:
            os.chmod(output_path, 0o666)  # Reset permissions

def test_generate_structure_with_header_and_footer():
    """Test generate_structure with header and footer files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        header_path = os.path.join(tmpdir, '.mapheader')
        footer_path = os.path.join(tmpdir, '.mapfooter')
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write('Header Content\n\n')
        with open(footer_path, 'w', encoding='utf-8') as f:
            f.write('Footer Content\n\n')
        with open(os.path.join(tmpdir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('File Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': header_path,
            'footer': footer_path,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'Header Content' in content
        assert 'Footer Content' in content
        assert 'file.txt' in content

def test_traverse_directory_with_ignore_patterns():
    """Test traverse_directory with ignore patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'dir_to_ignore'))
        with open(os.path.join(tmpdir, 'dir_to_ignore', 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Should be ignored')
        os.makedirs(os.path.join(tmpdir, 'dir_to_include'))
        with open(os.path.join(tmpdir, 'dir_to_include', 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Should be included')

        ignore_spec = PathSpec.from_lines('gitwildmatch', ['dir_to_ignore/'])
        omit_spec = PathSpec.from_lines('gitwildmatch', [])
        patterns = (ignore_spec, omit_spec)
        structure, file_contents = traverse_directory(tmpdir, patterns, ignore_hidden=True)
        assert 'dir_to_ignore' not in structure
        assert 'dir_to_include' in structure

def test_traverse_directory_with_omit_patterns():
    """Test traverse_directory with omit patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'dir_to_omit'))
        with open(os.path.join(tmpdir, 'dir_to_omit', 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Should be omitted')
        os.makedirs(os.path.join(tmpdir, 'dir_to_include'))
        with open(os.path.join(tmpdir, 'dir_to_include', 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Should be included')

        ignore_spec = PathSpec.from_lines('gitwildmatch', [])
        omit_spec = PathSpec.from_lines('gitwildmatch', ['dir_to_omit/'])
        patterns = (ignore_spec, omit_spec)
        structure, file_contents = traverse_directory(tmpdir, patterns, ignore_hidden=True)
        assert 'dir_to_omit' in structure
        assert structure['dir_to_omit'] == {'[omitted]': None}
        assert 'dir_to_include' in structure

def test_strip_empty_lines_edge_cases():
    """Test strip_empty_lines with only empty lines."""
    text = "\n\n   \n"
    expected = ''
    result = strip_empty_lines(text)
    assert result == expected

def test_generate_markdown_with_no_files():
    """Test generate_markdown when there are no files in file_contents."""
    structure = {
        'Folder': {}
    }
    file_contents = {}
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    output = generate_markdown(structure, file_contents, settings)
    expected_output = textwrap.dedent("""\
        Project Repository Structure:

        -> Folder
        """)
    assert output.strip() == expected_output.strip()

def test_generate_markdown_with_custom_settings():
    """Test generate_markdown with custom indent and arrow."""
    structure = {
        'Folder': {
            'File.txt': None
        }
    }
    file_contents = {
        'Folder/File.txt': 'Content'
    }
    settings = {
        'arrow': '-->',
        'indent_char': '....',
        'ignore_hidden': True,
        'max_size': 1000
    }
    output = generate_markdown(structure, file_contents, settings)
    expected_output = textwrap.dedent(f"""\
        Project Repository Structure:

        --> Folder
        ....--> File.txt

        ---

        Folder{os.sep}File.txt:

        ```
        Content
        ```
        """)
    assert output.strip() == expected_output.strip()

def test_generate_markdown_with_omitted_files():
    """Test generate_markdown where files are omitted."""
    structure = {
        'Folder': {
            'File.txt': None,
            'Secret.txt': None
        }
    }
    file_contents = {
        'Folder/File.txt': 'Content',
        'Folder/Secret.txt': '[omitted]'
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000
    }
    output = generate_markdown(structure, file_contents, settings)
    assert 'Secret.txt' in output
    assert '[omitted]' in output

def test_generate_structure_with_empty_settings():
    """Test generate_structure with empty settings dictionary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = {}
        with pytest.raises(KeyError):
            generate_structure(settings, root=tmpdir)

def test_traverse_directory_with_ignore_hidden_false():
    """Test traverse_directory with ignore_hidden set to False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, '.hidden_file'), 'w', encoding='utf-8') as f:
            f.write('Hidden content')
        with open(os.path.join(tmpdir, 'visible_file'), 'w', encoding='utf-8') as f:
            f.write('Visible content')
        patterns = (PathSpec.from_lines('gitwildmatch', []), PathSpec.from_lines('gitwildmatch', []))
        structure, file_contents = traverse_directory(tmpdir, patterns, ignore_hidden=False)
        assert '.hidden_file' in structure
        assert 'visible_file' in structure

def test_generate_structure_with_different_indentation():
    """Test generate_structure with different indentation characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'dir'))
        with open(os.path.join(tmpdir, 'dir', 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '--',
            'arrow': '=>',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert '=>' in content
        assert '--' in content  # Indentation

def test_generate_structure_with_no_files():
    """Test generate_structure when there are no files in the directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'empty_dir'))
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'empty_dir' in content

def test_generate_structure_with_relative_paths():
    """Test generate_structure when relative paths are provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        os.makedirs('dir')
        with open('dir/file.txt', 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': '.map',
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        try:
            generate_structure(settings)
            with open('.map', 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'dir' in content
            assert 'file.txt' in content
        finally:
            os.chdir(original_cwd)

def test_generate_structure_with_different_root():
    """Test generate_structure with a specified root directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = os.path.join(tmpdir, 'root')
        os.makedirs(root_dir)
        with open(os.path.join(root_dir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=root_dir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'file.txt' in content
        assert 'root' not in content  # Since root is set, 'root' should not be in the output

def test_generate_structure_with_invalid_ignore_file():
    """Test generate_structure when ignore file is invalid or unreadable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ignore_path = os.path.join(tmpdir, '.mapignore')
        with open(ignore_path, 'w', encoding='utf-8') as f:
            f.write('invalid_pattern[)\n')
        with open(os.path.join(tmpdir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'ignore': ignore_path,
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        # PathSpec doesn't raise exception on invalid patterns, so this should work
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'file.txt' in content

def test_traverse_directory_with_nonexistent_root():
    """Test traverse_directory when root directory does not exist."""
    tmpdir = '/nonexistent_directory'
    patterns = (PathSpec.from_lines('gitwildmatch', []), PathSpec.from_lines('gitwildmatch', []))
    with pytest.raises(FileNotFoundError):
        traverse_directory(tmpdir, patterns, ignore_hidden=True)

def test_generate_structure_with_invalid_max_size():
    """Test generate_structure with invalid max_size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': -1,  # Invalid max_size
            'verbose': False,
            'quiet': False
        }
        # Assuming generate_structure should raise ValueError for invalid max_size
        with pytest.raises(ValueError):
            generate_structure(settings, root=tmpdir)

def test_generate_structure_with_max_size_zero():
    """Test generate_structure with max_size set to zero."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 0,  # max_size zero should result in empty content
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'file.txt' in content
        # Extract the content of the file from the markdown
        match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
        assert match is not None
        file_content = match.group(1).strip()
        assert file_content == ''

def test_generate_structure_with_max_size_none():
    """Test generate_structure with max_size set to None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'file.txt'), 'w', encoding='utf-8') as f:
            f.write('Content' * 1000)
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            # Provide valid paths for 'ignore' and 'omit' to prevent TypeError
            'ignore': os.path.join(tmpdir, '.mapignore'),
            'omit': os.path.join(tmpdir, '.mapomit'),
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': None,  # Should read entire file
            'verbose': False,
            'quiet': False
        }
        # Create empty .mapignore and .mapomit files
        open(settings['ignore'], 'a').close()
        open(settings['omit'], 'a').close()
        # Depending on your implementation, if max_size=None is allowed, adjust the test accordingly
        # If it's not allowed and should raise an error, keep the assertion
        with pytest.raises(TypeError):
            generate_structure(settings, root=tmpdir)

def test_generate_structure_with_large_number_of_files():
    """Test generate_structure with a large number of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(1000):
            with open(os.path.join(tmpdir, f'file_{i}.txt'), 'w', encoding='utf-8') as f:
                f.write(f'Content {i}')
        settings = {
            'output': os.path.join(tmpdir, '.map'),
            'header': None,
            'footer': None,
            'indent_char': '\t',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000,
            'verbose': False,
            'quiet': False
        }
        generate_structure(settings, root=tmpdir)
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()
        for i in range(1000):
            assert f'file_{i}.txt' in content
