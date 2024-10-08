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
