"""
Logic to merge configuration defaults, file-based config, and CLI overrides.
"""

from mapper.core.defaults import DEFAULT_CONFIG

def merge_config_with_defaults(file_config, cli_kwargs):
    """
    Merge configuration defaults, file-based config, and CLI overrides.
    CLI overrides have the highest precedence, followed by the .mapconfig file,
    then the defaults.
    """
    merged = dict(DEFAULT_CONFIG)
    for k, v in file_config.items():
        merged[k] = v

    for k, v in cli_kwargs.items():
        if v is not None:
            merged[k] = v

    return merged
