import os
import json
from mapper.config import reset_settings as config_reset_settings, load_user_settings
from mapper.utils import load_patterns, read_file_content
import fnmatch

def get_version():
    return "0.1.0"

def reset_settings():
    config_reset_settings()

def traverse_directory(root, patterns, ignore_hidden=True):
    structure = {}
    ignore_spec, omit_spec = patterns
    for dirpath, dirnames, filenames in os.walk(root):
        if ignore_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]
        rel_path = os.path.relpath(dirpath, root)
        if rel_path == ".":
            rel_path = ""
        current = structure
        if rel_path:
            for part in rel_path.split(os.sep):
                current = current.setdefault(part, {})
        for dirname in dirnames:
            if dirname not in current:
                current[dirname] = {}
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            rel_file_path = os.path.join(rel_path, filename)
            if ignore_spec.match_file(rel_file_path):
                continue
            if omit_spec.match_file(rel_file_path):
                current[filename] = "[Content Omitted]"
            else:
                content = read_file_content(file_path, max_size=1000000)
                current[filename] = content
    return structure

def generate_markdown(structure, settings):
    lines = []
    arrow = settings.get('arrow', '-->')
    indent_char = settings.get('indent_char', '  ')
    
    def recurse(d, depth=0):
        for key, value in sorted(d.items()):
            lines.append(f"{indent_char * depth}{key}")
            if isinstance(value, dict):
                recurse(value, depth + 1)
            else:
                lines.append(f"{indent_char * (depth + 1)}{arrow} {value}")
    
    recurse(structure)
    return "\n".join(lines)

def generate_structure(settings):
    ignore_path = settings.get('ignore', '.mapignore')
    omit_path = settings.get('omit', '.mapomit')
    ignore_spec, omit_spec = load_patterns(ignore_path, omit_path)
    structure = traverse_directory(os.getcwd(), (ignore_spec, omit_spec), ignore_hidden=settings.get('ignore_hidden', True))
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
