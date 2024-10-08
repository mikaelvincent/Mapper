import os
from mapper.config import reset_settings as config_reset_settings
from mapper.utils import load_patterns, read_file_content

def get_version():
    return "0.1.0"

def reset_settings():
    config_reset_settings()

def traverse_directory(root, patterns, ignore_hidden=True, max_size=1000000):
    structure = {}
    file_contents = {}  # New dictionary to store file paths and contents
    ignore_spec, omit_spec = patterns
    for dirpath, dirnames, filenames in os.walk(root):
        rel_path = os.path.relpath(dirpath, root)
        if rel_path == ".":
            rel_path = ""
        # Prune dirnames based on ignore patterns and hidden directories
        dirnames[:] = [d for d in dirnames if not (
            (ignore_hidden and d.startswith('.')) or
            ignore_spec.match_file(os.path.join(rel_path, d) + '/')
        )]
        # Prune filenames based on ignore patterns and hidden files
        filenames = [f for f in filenames if not (
            (ignore_hidden and f.startswith('.')) or
            ignore_spec.match_file(os.path.join(rel_path, f))
        )]
        current = structure
        if rel_path:
            for part in rel_path.split(os.sep):
                current = current.setdefault(part, {})
        for dirname in dirnames:
            current.setdefault(dirname, {})
        for filename in filenames:
            rel_file_path = os.path.join(rel_path, filename)
            file_path = os.path.join(dirpath, filename)
            current[filename] = None  # Indicate that this is a file
            if not omit_spec.match_file(rel_file_path):
                content = read_file_content(file_path, max_size=max_size)
                file_contents[rel_file_path] = content
            else:
                file_contents[rel_file_path] = "[Content Omitted]"
    return structure, file_contents

def generate_markdown(structure, file_contents, settings):
    lines = ['Project Repository Structure:\n']
    arrow = settings.get('arrow', '-->')
    indent_char = settings.get('indent_char', '\t')  # Default is now '\t'

    def recurse(d, depth=0):
        # Sort items: directories first, then files
        items = list(d.items())
        items.sort(key=lambda x: (0, x[0]) if isinstance(x[1], dict) else (1, x[0]))
        for key, value in items:
            lines.append(f"{indent_char * depth}{arrow} {key}")
            if isinstance(value, dict):
                recurse(value, depth + 1)
            # No else block needed here

    recurse(structure)

    # Now add the file contents at the bottom
    if file_contents:
        lines.append('\n---\n')
        for file_path, content in sorted(file_contents.items()):
            # Replace '/' with '\\' for Windows-style paths
            display_path = file_path.replace('/', os.sep)
            lines.append(f"{display_path}:\n")
            lines.append("```\n" + content + "\n```\n")
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
            header = f.read().strip() + "\n\n"
    if settings.get('footer') and os.path.exists(settings['footer']):
        with open(settings['footer'], 'r', encoding='utf-8') as f:
            footer = "\n\n" + f.read().strip()
    with open(settings['output'], 'w', encoding='utf-8') as f:
        f.write(header + markdown + footer)
