import os
from mapper.utils import load_patterns, read_file_content, normalize_path

def strip_empty_lines(text):
    lines = text.split('\n')
    while lines and lines[0].strip() == '':
        lines.pop(0)
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
        rel_path_normalized = normalize_path(rel_path)

        if omit_spec.match_file(rel_path_normalized + '/'):
            current = structure
            if rel_path_normalized:
                for part in rel_path_normalized.split('/'):
                    current = current.setdefault(part, {})
            current["[omitted]"] = None
            dirnames[:] = []
            filenames[:] = []
            continue

        dirnames[:] = [d for d in dirnames if not (
            (ignore_hidden and d.startswith('.')) or
            ignore_spec.match_file(normalize_path(os.path.join(rel_path, d)) + '/')
        )]

        filenames = [f for f in filenames if not (
            (ignore_hidden and f.startswith('.')) or
            ignore_spec.match_file(normalize_path(os.path.join(rel_path, f)))
        )]

        current = structure
        if rel_path_normalized:
            for part in rel_path_normalized.split('/'):
                current = current.setdefault(part, {})

        for dirname in dirnames:
            current.setdefault(dirname, {})

        for filename in filenames:
            rel_file_path = normalize_path(os.path.join(rel_path, filename))
            file_path = os.path.join(dirpath, filename)
            current[filename] = None
            if not omit_spec.match_file(rel_file_path):
                content = read_file_content(file_path, max_size=max_size)
                file_contents[rel_file_path] = content
            else:
                file_contents[rel_file_path] = "[omitted]"

    return structure, file_contents

def generate_markdown(structure, file_contents, settings):
    lines = ['Project Repository Structure:\n']
    arrow = settings.get('arrow', '->')
    indent_char = settings.get('indent_char', '\t')

    file_paths_in_order = []

    def recurse(d, depth=0, path=''):
        items = list(d.items())
        items.sort(key=lambda x: (0, x[0]) if isinstance(x[1], dict) else (1, x[0]))
        for key, value in items:
            if key == "[omitted]":
                lines.append(f"{indent_char * depth}{arrow} [omitted]")
                continue

            lines.append(f"{indent_char * depth}{arrow} {key}")
            new_path = os.path.join(path, key) if path else key
            if isinstance(value, dict):
                if "[omitted]" in value:
                    lines.append(f"{indent_char * (depth + 1)}{arrow} [omitted]")
                else:
                    recurse(value, depth + 1, new_path)
            else:
                file_paths_in_order.append(normalize_path(new_path))

    recurse(structure)

    if file_contents:
        lines.append('\n---\n')
        num_files = len(file_paths_in_order)
        for i, file_path in enumerate(file_paths_in_order):
            content = file_contents.get(file_path, '[omitted]')
            display_path = file_path.replace('/', os.sep)
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
