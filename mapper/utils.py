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
