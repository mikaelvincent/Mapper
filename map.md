Project Repository Structure:

-> mapper
  -> __init__.py
  -> cli.py
  -> config.py
  -> core.py
  -> utils.py
-> tests
  -> __init__.py
  -> test_cli.py
  -> test_config.py
  -> test_core.py
  -> test_utils.py
-> setup.py

---

mapper\__init__.py:

```
__version__ = "0.1.0"

```

---

mapper\cli.py:

```
import click
from mapper.core import generate_structure, reset_settings, get_version
from mapper.config import save_user_settings, load_user_settings, DEFAULT_SETTINGS

@click.group()
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable detailed output.')
@click.option('-q', '--quiet', is_flag=True, default=False, help='Suppress non-essential messages.')
@click.option('--save-settings', is_flag=True, default=False, help='Store current options for future invocations.')
@click.option('--load-settings', is_flag=True, default=False, help='Load previously saved settings.')
@click.pass_context
def main(ctx, verbose, quiet, save_settings, load_settings):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet
    ctx.obj['SAVE_SETTINGS'] = save_settings
    ctx.obj['LOAD_SETTINGS'] = load_settings
    if load_settings:
        settings = load_user_settings()
        ctx.obj.update(settings)

@main.command()
def version():
    """Display Mapper's current version."""
    version = get_version()
    click.echo(f"Mapper version {version}")

@main.command(name='reset-settings')
@click.pass_context
def reset_settings_command(ctx):
    """Reset all stored settings to their default values."""
    reset_settings()
    click.echo("Settings have been reset to default values.")

@main.command()
@click.option('-o', '--output', default='map.md', help='Specify output file name.')
@click.option('-i', '--ignore', default='.mapignore', help='Specify custom ignore file.')
@click.option('-H', '--header', default='.mapheader', help='Specify custom header file.')
@click.option('-F', '--footer', default='.mapfooter', help='Specify custom footer file.')
@click.option('-a', '--indent-char', default='  ', help='Choose indentation character.')
@click.option('--arrow', default='->', help='Customize arrow symbol.')
@click.option('--ignore-hidden', type=bool, default=True, help='Toggle to ignore hidden files.')
@click.option('--max-size', type=int, default=1000000, help='Set maximum file size before truncation in bytes.')
@click.pass_context
def generate(ctx, output, ignore, header, footer, indent_char, arrow, ignore_hidden, max_size):
    """Creates the project structure output."""
    settings = {
        'output': output,
        'ignore': ignore,
        'header': header,
        'footer': footer,
        'indent_char': indent_char,
        'arrow': arrow,
        'ignore_hidden': ignore_hidden,
        'max_size': max_size,
        'verbose': ctx.obj.get('VERBOSE', False),
        'quiet': ctx.obj.get('QUIET', False)
    }
    if ctx.obj.get('SAVE_SETTINGS', False):
        save_user_settings(settings)
    generate_structure(settings)
    if not ctx.obj.get('QUIET', False):
        click.echo("Project structure generated")

if __name__ == '__main__':
    main()

```

---

mapper\config.py:

```
import json
import os

DEFAULT_SETTINGS = {
    'output': 'map.md',
    'ignore': '.mapignore',
    'header': '.mapheader',
    'footer': '.mapfooter',
    'indent_char': '\t',
    'arrow': '->',
    'ignore_hidden': True,
    'max_size': 1000000,
    'verbose': False,
    'quiet': False
}

CONFIG_FILE = os.path.expanduser('~/.mapconfig')

def save_user_settings(settings):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_user_settings():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_SETTINGS.copy()
    with open(CONFIG_FILE, 'r') as f:
        try:
            settings = json.load(f)
            return {**DEFAULT_SETTINGS, **settings}
        except json.JSONDecodeError:
            return DEFAULT_SETTINGS.copy()

def reset_settings():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

```

---

mapper\core.py:

```
import os
from mapper.config import reset_settings as config_reset_settings
from mapper.utils import load_patterns, read_file_content, normalize_path

def get_version():
    return "0.1.0"

def reset_settings():
    config_reset_settings()

def strip_empty_lines(text):
    lines = text.split('\n')
    # Remove empty lines at the start
    while lines and lines[0].strip() == '':
        lines.pop(0)
    # Remove empty lines at the end
    while lines and lines[-1].strip() == '':
        lines.pop()
    return '\n'.join(lines)

def traverse_directory(root, patterns, ignore_hidden=True, max_size=1000000):
    structure = {}
    file_contents = {}
    ignore_spec, omit_spec = patterns
    for dirpath, dirnames, filenames in os.walk(root):
        rel_path = os.path.relpath(dirpath, root)
        if rel_path == ".":
            rel_path = ""
        rel_path_normalized = normalize_path(rel_path)  # Normalize rel_path to POSIX-style

        # Check if the current directory is omitted
        if omit_spec.match_file(rel_path_normalized + '/'):
            # Mark the directory as omitted
            current = structure
            if rel_path_normalized:
                for part in rel_path_normalized.split('/'):  # Use '/' as separator
                    current = current.setdefault(part, {})
            current["[omitted]"] = None
            # Do not traverse into this directory
            dirnames[:] = []
            filenames[:] = []
            continue

        # Normalize and filter directory names
        dirnames[:] = [d for d in dirnames if not (
            (ignore_hidden and d.startswith('.')) or
            ignore_spec.match_file(normalize_path(os.path.join(rel_path, d)) + '/')
        )]

        # Normalize and filter file names
        filenames = [f for f in filenames if not (
            (ignore_hidden and f.startswith('.')) or
            ignore_spec.match_file(normalize_path(os.path.join(rel_path, f)))
        )]

        current = structure
        if rel_path_normalized:
            for part in rel_path_normalized.split('/'):  # Use '/' as separator
                current = current.setdefault(part, {})

        for dirname in dirnames:
            current.setdefault(dirname, {})

        for filename in filenames:
            rel_file_path = normalize_path(os.path.join(rel_path, filename))
            file_path = os.path.join(dirpath, filename)
            current[filename] = None  # Indicate that this is a file
            if not omit_spec.match_file(rel_file_path):
                content = read_file_content(file_path, max_size=max_size)
                file_contents[rel_file_path] = content
            else:
                file_contents[rel_file_path] = "[omitted]"  # Changed from "[Content Omitted]"

    return structure, file_contents

def generate_markdown(structure, file_contents, settings):
    lines = ['Project Repository Structure:\n']
    arrow = settings.get('arrow', '->')
    indent_char = settings.get('indent_char', '\t')

    file_paths_in_order = []

    def recurse(d, depth=0, path=''):
        # Sort items: directories first, then files
        items = list(d.items())
        items.sort(key=lambda x: (0, x[0]) if isinstance(x[1], dict) else (1, x[0]))
        for key, value in items:
            if key == "[omitted]":
                lines.append(f"{indent_char * depth}{arrow} [omitted]")
                continue

            lines.append(f"{indent_char * depth}{arrow} {key}")
            new_path = os.path.join(path, key) if path else key
            if isinstance(value, dict):
                # Check if the directory is marked as omitted
                if "[omitted]" in value:
                    lines.append(f"{indent_char * (depth + 1)}{arrow} [omitted]")
                else:
                    recurse(value, depth + 1, new_path)
            else:
                file_paths_in_order.append(normalize_path(new_path))  # Normalize path

    recurse(structure)

    # Add the file contents in the same order as they appeared during recursion
    if file_contents:
        lines.append('\n---\n')
        num_files = len(file_paths_in_order)
        for i, file_path in enumerate(file_paths_in_order):
            content = file_contents.get(file_path, '[omitted]')
            display_path = file_path.replace('/', os.sep)  # Use OS-specific separator
            lines.append(f"{display_path}:\n")
            lines.append(f"```\n{content}\n```\n")
            if i < num_files - 1:
                lines.append('---\n')

    return "\n".join(lines)

def generate_structure(settings, root=None):
    if root is None:
        root = os.getcwd()
    ignore_path = settings.get('ignore', '.mapignore')
    omit_path = settings.get('omit', '.mapomit')
    ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
    structure, file_contents = traverse_directory(
        root,
        (ignore_spec, omit_spec),
        ignore_hidden=settings.get('ignore_hidden', True),
        max_size=settings.get('max_size', 1000000)
    )
    markdown = generate_markdown(structure, file_contents, settings)
    header = ""
    footer = ""
    if settings.get('header') and os.path.exists(settings['header']):
        with open(settings['header'], 'r', encoding='utf-8') as f:
            header_content = f.read()
            header = strip_empty_lines(header_content) + "\n\n---\n\n"
    if settings.get('footer') and os.path.exists(settings['footer']):
        with open(settings['footer'], 'r', encoding='utf-8') as f:
            footer_content = f.read()
            footer = "\n---\n\n" + strip_empty_lines(footer_content) + "\n"
    with open(settings['output'], 'w', encoding='utf-8') as f:
        f.write(header + markdown + footer)

```

---

mapper\utils.py:

```
# mapper/utils.py

import os
from pathspec import PathSpec

def normalize_path(path):
    return path.replace(os.sep, '/')

def load_patterns(ignore_path, omit_path):
    ignore_patterns = []
    omit_patterns = []

    # Mapper-related files to always exclude
    default_ignore = ['.mapignore', 'map.md', '.mapheader', '.mapfooter', '.mapomit', '.mapconfig']
    default_omit = ['.mapignore', 'map.md', '.mapheader', '.mapfooter', '.mapomit', '.mapconfig']

    if os.path.exists(ignore_path):
        with open(ignore_path, 'r') as f:
            user_ignore = [
                normalize_path(line.strip()) 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
            ignore_patterns.extend(user_ignore)

    if os.path.exists(omit_path):
        with open(omit_path, 'r') as f:
            user_omit = [
                normalize_path(line.strip()) 
                for line in f 
                if line.strip() and not line.startswith('#')
            ]
            omit_patterns.extend(user_omit)

    # Always exclude Mapper-related files
    ignore_patterns.extend(default_ignore)
    omit_patterns.extend(default_omit)

    ignore_spec = PathSpec.from_lines('gitwildmatch', ignore_patterns)
    omit_spec = PathSpec.from_lines('gitwildmatch', omit_patterns)
    return ignore_spec, omit_spec

def read_file_content(file_path, max_size=1000000):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(max_size + 1)
            if len(content) > max_size:
                return content[:max_size] + '... [Truncated]'
            return content
    except (UnicodeDecodeError, OSError):
        return '[Content Unreadable]'

def is_hidden(filepath):
    return any(part.startswith('.') for part in filepath.split(os.sep))

```

---

tests\__init__.py:

```

```

---

tests\test_cli.py:

```
import pytest
from click.testing import CliRunner
from mapper.cli import main
import os
import tempfile

@pytest.fixture
def temp_config_file(monkeypatch):
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        config_file = tf.name
    monkeypatch.setattr('mapper.config.CONFIG_FILE', config_file)
    yield config_file
    if os.path.exists(config_file):
        os.remove(config_file)

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['version'])
    assert result.exit_code == 0
    assert 'Mapper version' in result.output

def test_generate_default(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure 'map.md' is created
        assert os.path.exists('map.md')

def test_generate_with_custom_output(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--output', 'custom_map.md'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure 'custom_map.md' is created
        assert os.path.exists('custom_map.md')

def test_reset_settings(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a dummy settings file
        with open(temp_config_file, 'w') as f:
            f.write('{}')
        result = runner.invoke(main, ['reset-settings'])
        assert result.exit_code == 0
        assert 'Settings have been reset to default values.' in result.output
        # Ensure the settings file is removed
        assert not os.path.exists(temp_config_file)

def test_generate_with_ignore_hidden(temp_config_file):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['generate', '--ignore-hidden', 'false'])
        assert result.exit_code == 0
        assert 'Project structure generated' in result.output
        # Ensure 'map.md' is created
        assert os.path.exists('map.md')

def test_invalid_subcommand():
    runner = CliRunner()
    result = runner.invoke(main, ['invalid'])
    assert result.exit_code != 0
    assert 'No such command' in result.output

```

---

tests\test_config.py:

```
import pytest
import os
import tempfile
from mapper.config import save_user_settings, load_user_settings, DEFAULT_SETTINGS

@pytest.fixture
def temp_config_file():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()  # Ensure the file is closed before yielding
    yield tf.name
    if os.path.exists(tf.name):
        os.remove(tf.name)

def test_default_settings():
    assert DEFAULT_SETTINGS == {
        'output': 'map.md',
        'ignore': '.mapignore',
        'header': '.mapheader',
        'footer': '.mapfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': True,
        'max_size': 1000000,
        'verbose': False,
        'quiet': False
    }

def test_save_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_map.md',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': False
    }
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    with open(temp_config_file, 'r') as f:
        loaded_settings = f.read()
    assert '"output": "custom_map.md"' in loaded_settings
    assert '"ignore_hidden": false' in loaded_settings

def test_load_user_settings(temp_config_file, monkeypatch):
    settings = {
        'output': 'custom_map.md',
        'ignore': '.customignore',
        'header': '.customheader',
        'footer': '.customfooter',
        'indent_char': '\t',
        'arrow': '->',
        'ignore_hidden': False,
        'max_size': 500000,
        'verbose': True,
        'quiet': False
    }
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    save_user_settings(settings)
    loaded_settings = load_user_settings()
    assert loaded_settings == settings

def test_load_user_settings_default(temp_config_file, monkeypatch):
    monkeypatch.setattr('mapper.config.CONFIG_FILE', temp_config_file)
    # Ensure the config file does not exist
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)
    loaded_settings = load_user_settings()
    assert loaded_settings == DEFAULT_SETTINGS

```

---

tests\test_core.py:

```
import pytest
import os
import tempfile
import textwrap
from unittest.mock import patch, MagicMock
from mapper.core import generate_structure, reset_settings, get_version, traverse_directory, load_patterns, generate_markdown
from pathspec import PathSpec

def test_generate_structure_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': os.path.join(tmpdir, '.mapignore'),
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
            with open(settings['output'], 'r') as f:
                content = f.read()
        assert content.strip() == 'Project Repository Structure:'

def test_traverse_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample directory structure
        os.makedirs(os.path.join(tmpdir, 'src'))
        with open(os.path.join(tmpdir, 'src', 'main.py'), 'w') as f:
            f.write("# main.py")
        with open(os.path.join(tmpdir, 'README.md'), 'w') as f:
            f.write("# README")
        
        patterns = (PathSpec.from_lines('gitwildmatch', []), PathSpec.from_lines('gitwildmatch', []))  # No ignore or omit patterns
        structure, file_contents = traverse_directory(tmpdir, patterns, ignore_hidden=True)
        expected_structure = {
            'src': {
                'main.py': None
            },
            'README.md': None
        }
        expected_file_contents = {
            'src/main.py': '# main.py',
            'README.md': '# README'
        }
        assert structure == expected_structure
        assert file_contents == expected_file_contents

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
        
        structure, file_contents = traverse_directory(tmpdir, (patterns_ignore, patterns_omit), ignore_hidden=True)
        expected_structure = {
            'src': {
                'main.py': None,
                'secret.py': None
            }
        }
        expected_file_contents = {
            'src/main.py': '# main.py',
            'src/secret.py': '[omitted]'
        }
        assert structure == expected_structure
        assert file_contents == expected_file_contents

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
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }

        generate_structure(settings, root=tmpdir)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()

        # Use os.path.join to create platform-independent expected paths
        expected_display_path = os.path.join('src', 'main.py')

        expected_content = textwrap.dedent(f"""\
            Project Repository Structure:

            -> src
              -> main.py

            ---

            {expected_display_path}:

            ```
            # main.py
            ```
            """)

        assert content.strip() == expected_content.strip()

def test_generate_structure_with_omitted_empty_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup directory structure with an omitted empty folder
        os.makedirs(os.path.join(tmpdir, 'empty_folder'))
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(omit_path, 'w', encoding='utf-8') as f:
            f.write('empty_folder/\n')

        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': os.path.join(tmpdir, '.mapignore'),
            'omit': omit_path,
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }

        generate_structure(settings, root=tmpdir)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()

        expected_content = textwrap.dedent("""\
            Project Repository Structure:

            -> empty_folder
              -> [omitted]
            """)

        assert content.strip() == expected_content.strip()

def test_generate_structure_with_omitted_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup directory structure with an omitted file
        with open(os.path.join(tmpdir, 'secret.txt'), 'w', encoding='utf-8') as f:
            f.write("Top Secret")
        omit_path = os.path.join(tmpdir, '.mapomit')
        with open(omit_path, 'w', encoding='utf-8') as f:
            f.write('secret.txt\n')

        settings = {
            'output': os.path.join(tmpdir, 'map.md'),
            'ignore': os.path.join(tmpdir, '.mapignore'),
            'omit': omit_path,
            'header': None,
            'footer': None,
            'indent_char': '  ',
            'arrow': '->',
            'ignore_hidden': True,
            'max_size': 1000000,
            'verbose': False,
            'quiet': False
        }

        generate_structure(settings, root=tmpdir)
        assert os.path.exists(settings['output'])
        with open(settings['output'], 'r', encoding='utf-8') as f:
            content = f.read()

        expected_content = textwrap.dedent("""\
            Project Repository Structure:

            -> secret.txt

            ---

            secret.txt:

            ```
            [omitted]
            ```
            """)

        assert content.strip() == expected_content.strip()

def test_generate_markdown_output_format():
    # Setup a simple structure and file_contents
    structure = {
        'File1.txt': None,
        'Folder1': {
            'File2.txt': None
        }
    }
    file_contents = {
        'File1.txt': '[omitted]',
        'Folder1/File2.txt': '[omitted]'
    }
    settings = {
        'arrow': '->',
        'indent_char': '  ',
        'ignore_hidden': True,
        'max_size': 1000000
    }
    output = generate_markdown(structure, file_contents, settings)
    # Split output into lines
    lines = output.strip().split('\n')
    # Ensure the last line is not an extra '---'
    if len(lines) >= 2:
        assert lines[-1] != '---'

```

---

tests\test_utils.py:

```
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

```

---

setup.py:

```
from setuptools import setup, find_packages

setup(
    name='Mapper',
    version='0.1.0',
    description='A command-line tool to generate a customizable representation of a project\'s directory and file structure.',
    author='mikaelvincent.dev',
    author_email='tumampos@mikaelvincent.dev',
    packages=find_packages(),
    install_requires=[
        'click>=8.0',
        'pathspec>=0.9.0'
    ],
    entry_points={
        'console_scripts': [
            'map=mapper.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

```

---

Additionally, indicate which branch to commit in in your output. You may create new branches if needed. Generate a commit message as well.

---

Modify. Change default output to .map instead of mad.md. Adjust any tests accordingly.
