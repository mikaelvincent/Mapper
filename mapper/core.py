import os
from mapper.config import reset_settings as config_reset_settings
from mapper.utils import load_patterns, read_file_content

def get_version():
    return "0.1.0"

def reset_settings():
    config_reset_settings()

def traverse_directory(root, patterns, ignore_hidden=True, max_size=1000000):
    structure = {}
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
            if omit_spec.match_file(rel_file_path):
                current[filename] = "[Content Omitted]"
            else:
                content = read_file_content(file_path, max_size=max_size)
                current[filename] = content
    return structure

def generate_markdown(structure, settings):
    lines = ['Project Repository Structure:\n']
    arrow = settings.get('arrow', '-->')
    indent_char = settings.get('indent_char', '  ')

    def recurse(d, depth=0):
        # Sort items: directories first, then files
        items = list(d.items())
        items.sort(key=lambda x: (0, x[0]) if isinstance(x[1], dict) else (1, x[0]))
        for key, value in items:
            lines.append(f"{indent_char * depth}{arrow} {key}")
            if isinstance(value, dict):
                recurse(value, depth + 1)

    recurse(structure)
    return "\n".join(lines)

def generate_structure(settings, root=None):
    if root is None:
        root = os.getcwd()
    ignore_path = settings.get('ignore', '.mapignore')
    omit_path = settings.get('omit', '.mapomit')
    ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
    structure = traverse_directory(
        root,
        (ignore_spec, omit_spec),
        ignore_hidden=settings.get('ignore_hidden', True),
        max_size=settings.get('max_size', 1000000)
    )
    markdown = generate_markdown(structure, settings)
    header = ""
    footer = ""
    if settings.get('header') and os.path.exists(settings['header']):
        with open(settings['header'], 'r') as f:
            header = f.read().strip() + "\n\n"
    if settings.get('footer') and os.path.exists(settings['footer']):
        with open(settings['footer'], 'r') as f:
            footer = "\n\n" + f.read().strip()
    with open(settings['output'], 'w') as f:
        f.write(header + markdown + footer)
