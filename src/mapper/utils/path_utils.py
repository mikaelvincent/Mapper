import os

def normalize_path(path):
    return path.replace(os.sep, '/')

def is_hidden(filepath):
    return any(part.startswith('.') for part in filepath.split(os.sep))
