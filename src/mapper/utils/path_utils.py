import os

def normalize_path(path):
    return path.replace(os.sep, '/')

def is_hidden(filepath):
    normalized_path = normalize_path(filepath)
    if normalized_path in ('.', '..'):
        return True
    parts = normalized_path.split('/')
    return any(
        part.startswith('.') and not (part in ('.', '..')) and not part.startswith('._')
        for part in parts
    )
