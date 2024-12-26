"""
CLI entry point for the Mapper tool.
"""

import click
import os
import sys

from . import __version__

# Default configuration values
DEFAULT_CONFIG = {
    "max_files": None,
    "max_characters_per_file": None,
    "ignore_hidden": True,
    "trim_trailing_whitespaces": True,
    "trim_all_empty_lines": False,
    "minimal_output": False,
    "use_absolute_path_title": False,
    "encodings": ["utf-8", "utf-16", "latin-1"]
}

def parse_mapconfig(config_path=".mapconfig"):
    """
    Parse the .mapconfig file if it exists. Return a dictionary
    of configuration settings. Lines starting with '#' are treated
    as comments and ignored. Configuration is assumed to be in
    'key=value' format.
    """
    config_data = {}
    if not os.path.isfile(config_path):
        return config_data

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Attempt basic type parsing
                if key in ("max_files", "max_characters_per_file"):
                    try:
                        config_data[key] = int(value)
                    except ValueError:
                        # Invalid integer; ignore or handle as needed
                        pass
                elif key in ("ignore_hidden", "trim_trailing_whitespaces",
                             "trim_all_empty_lines", "minimal_output",
                             "use_absolute_path_title"):
                    # Convert string to boolean
                    config_data[key] = value.lower() in ("true", "1", "yes")
                elif key == "encodings":
                    # Split on commas or spaces
                    enc_list = [v.strip() for v in value.replace(",", " ").split()]
                    config_data[key] = [enc for enc in enc_list if enc]
                else:
                    # Unrecognized or additional fields can be stored directly
                    config_data[key] = value
    except OSError:
        # If there's an issue reading the file, treat as empty config
        pass

    return config_data

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

def int_or_none(ctx, param, value):
    """
    Custom callback for Click to interpret a string of "None" as None,
    or otherwise parse the value as an integer.
    """
    if value is None:
        return None
    if value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter(f"Invalid integer value: {value}")

def bool_or_none(ctx, param, value):
    """
    Custom callback for Click to interpret possible strings as booleans
    if they are not None or 'None'.
    """
    if value is None:
        return None
    val_lower = value.lower()
    if val_lower == "none":
        return None
    return val_lower in ("true", "1", "yes")

@click.group()
@click.option("--max-files", callback=int_or_none, default=None, help="Override max_files.")
@click.option("--max-chars-per-file", callback=int_or_none, default=None, help="Override max_characters_per_file.")
@click.option("--ignore-hidden", callback=bool_or_none, default=None, help="Override ignore_hidden (true/false).")
@click.option("--trim-trailing-whitespaces", callback=bool_or_none, default=None, help="Override trim_trailing_whitespaces (true/false).")
@click.option("--trim-all-empty-lines", callback=bool_or_none, default=None, help="Override trim_all_empty_lines (true/false).")
@click.option("--minimal-output", callback=bool_or_none, default=None, help="Override minimal_output (true/false).")
@click.option("--use-absolute-path-title", callback=bool_or_none, default=None, help="Override use_absolute_path_title (true/false).")
def main(max_files,
         max_chars_per_file,
         ignore_hidden,
         trim_trailing_whitespaces,
         trim_all_empty_lines,
         minimal_output,
         use_absolute_path_title):
    """
    Main entry point for the Mapper CLI.
    Command-line options override .mapconfig and defaults where applicable.
    """
    cli_config = {
        "max_files": max_files,
        "max_characters_per_file": max_chars_per_file,
        "ignore_hidden": ignore_hidden,
        "trim_trailing_whitespaces": trim_trailing_whitespaces,
        "trim_all_empty_lines": trim_all_empty_lines,
        "minimal_output": minimal_output,
        "use_absolute_path_title": use_absolute_path_title
    }

    file_config = parse_mapconfig()
    merged_config = merge_config_with_defaults(file_config, cli_config)

    # Store final config in click's context object if needed
    ctx = click.get_current_context()
    ctx.obj = merged_config

@main.command()
def help():
    """
    Display placeholder help information.
    """
    click.echo("Placeholder help content")

@main.command()
def version():
    """
    Display placeholder version information.
    """
    click.echo(f"Mapper version: {__version__}")

@main.command()
def init():
    """
    Create Mapper-related files if they do not already exist.
    """
    files_to_create = [
        ".mapheader",
        ".mapfooter",
        ".mapignore",
        ".mapomit",
        ".mapinclude",
        ".mapconfig"
    ]

    for file_name in files_to_create:
        if not os.path.exists(file_name):
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    if file_name == ".mapconfig":
                        f.write("# Mapper configuration file\n")
                    else:
                        f.write("")
                click.echo(f"Created {file_name}")
            except OSError as e:
                click.echo(f"Could not create {file_name}: {str(e)}")
        else:
            click.echo(f"Skipped {file_name}, already exists.")

if __name__ == "__main__":
    main()
