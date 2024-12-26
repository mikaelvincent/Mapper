"""
Main CLI module for the Mapper tool.
"""

import click

from mapper.config.file_handling import parse_mapconfig, write_mapconfig
from mapper.core.defaults import DEFAULT_CONFIG
from mapper.core.merges import merge_config_with_defaults
from mapper.core.utils import int_or_none, bool_or_none

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

# Import subcommands to register them with the main group
from .commands.help_command import help_cmd
main.add_command(help_cmd)

from .commands.version_command import version_cmd
main.add_command(version_cmd)

from .commands.init_command import init_cmd
main.add_command(init_cmd)

from .commands.config_command import config_cmd
main.add_command(config_cmd)
