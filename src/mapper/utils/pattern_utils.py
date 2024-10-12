import os
from pathspec import PathSpec
from .path_utils import normalize_path

def load_patterns(ignore_path, omit_path):
    ignore_patterns = []
    omit_patterns = []

    default_ignore = ['.mapignore', '.map', '.mapheader', '.mapfooter', '.mapomit', '.mapconfig']
    default_omit = ['.mapignore', '.map', '.mapheader', '.mapfooter', '.mapomit', '.mapconfig']

    if os.path.exists(ignore_path):
        with open(ignore_path, 'r', encoding='utf-8') as f:
            user_ignore = [
                normalize_path(line.strip())
                for line in f
                if line.strip() and not line.startswith('#')
            ]
            ignore_patterns.extend(user_ignore)

    if os.path.exists(omit_path):
        with open(omit_path, 'r', encoding='utf-8') as f:
            user_omit = [
                normalize_path(line.strip())
                for line in f
                if line.strip() and not line.startswith('#')
            ]
            omit_patterns.extend(user_omit)

    ignore_patterns.extend(default_ignore)
    omit_patterns.extend(default_omit)

    ignore_spec = PathSpec.from_lines('gitwildmatch', ignore_patterns)
    omit_spec = PathSpec.from_lines('gitwildmatch', omit_patterns)
    return ignore_spec, omit_spec
