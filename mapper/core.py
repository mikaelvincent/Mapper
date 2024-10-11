import os
from mapper.config import reset_settings as config_reset_settings
from mapper.utils import load_patterns, read_file_content, normalize_path

def get_version():
    return "0.1.0"

def reset_settings():
    config_reset_settings()

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
            header = f.read().strip() + "\n\n"
    if settings.get('footer') and os.path.exists(settings['footer']):
        with open(settings['footer'], 'r', encoding='utf-8') as f:
            footer = "\n\n" + f.read().strip()
    with open(settings['output'], 'w', encoding='utf-8') as f:
        f.write(header + markdown + footer)
