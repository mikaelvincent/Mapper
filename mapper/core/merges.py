"""
Logic to merge configuration defaults, file-based config, and CLI overrides.
"""

from mapper.core.defaults import DEFAULT_CONFIG
import sys

def merge_config_with_defaults(file_config, cli_kwargs):
    """
    Merge configuration defaults, file-based config, and CLI overrides.
    CLI overrides have the highest precedence, followed by the .mapconfig file,
    then the defaults.

    To handle 'None' as a valid override, we detect if a parameter was
    explicitly provided in the CLI by checking sys.argv. If the parameter
    name is present, we apply the override even if it is None.
    """
    merged = dict(DEFAULT_CONFIG)

    # Merge file-based config
    for k, v in file_config.items():
        merged[k] = v

    # Special handling for known parameter naming mismatches.
    # The CLI option is '--max-chars-per-file', but the internal key is 'max_characters_per_file'.
    # We map them so that merges.py checks the correct CLI argument.
    param_name_map = {
        "max_characters_per_file": "--max-chars-per-file",
    }

    # Merge CLI overrides (check if user explicitly typed the parameter)
    for k in cli_kwargs:
        # Default dash_k using typical pattern
        dash_k = f"--{k.replace('_','-')}"

        # If there's a custom mapping, apply it
        if k in param_name_map:
            dash_k = param_name_map[k]

        if any(arg == dash_k or arg.startswith(dash_k + "=") for arg in sys.argv):
            merged[k] = cli_kwargs[k]

    return merged
