import os
import sys
import click

from mapper.core.filters import (
    parse_pattern_file,
    determine_inclusion_status
)
from mapper.core.utils import bool_or_none
from mapper.core.defaults import DEFAULT_CONFIG
import pyperclip

from mapper.core.traversal import (
    build_directory_tree,
    read_file_safely,
    SymlinkEncounteredError,
    ConstraintViolatedError
)


@click.command(name="generate")
@click.option("--output", "output_file", default=".map",
              help="Specify an alternate output file instead of .map.")
@click.option("--clipboard", is_flag=True,
              help="Copy the generated map content to the clipboard.")
def generate_cmd(output_file, clipboard):
    """
    Generate .map for the current directory, respecting .mapinclude,
    .mapignore, and .mapomit. Stops if symlinks are found or if
    file limits are exceeded.
    """
    ctx = click.get_current_context()
    config = ctx.obj if ctx.obj else dict(DEFAULT_CONFIG)

    include_patterns = parse_pattern_file(".mapinclude")
    if not include_patterns:
        include_patterns = []
    ignore_patterns = parse_pattern_file(".mapignore")
    omit_patterns = parse_pattern_file(".mapomit")

    mapheader_content = read_file_safely(".mapheader")
    mapfooter_content = read_file_safely(".mapfooter")

    try:
        content_lines = []
        if config.get("use_absolute_path_title", False):
            top_label = os.path.abspath(os.getcwd())
        else:
            top_label = os.path.basename(os.getcwd()) or os.getcwd()

        content_lines.append(top_label)
        content_lines.append("")  # Spacing line

        tree_lines = []
        file_count_tracker = [0]
        build_directory_tree(
            current_path=".",
            prefix="",
            lines=tree_lines,
            config=config,
            include_patterns=include_patterns,
            ignore_patterns=ignore_patterns,
            omit_patterns=omit_patterns,
            file_count_tracker=file_count_tracker,
            determine_inclusion_status=determine_inclusion_status
        )

        content_lines.extend(tree_lines)

        final_output = []
        if mapheader_content:
            final_output.append(mapheader_content.strip() + "\n")
        final_output.append("\n".join(content_lines))
        if mapfooter_content:
            final_output.append("\n---\n" + mapfooter_content.strip() + "\n")

        rendered_output = "\n".join(final_output)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_output + "\n")

        if clipboard:
            try:
                pyperclip.copy(rendered_output)
            except pyperclip.PyperclipException as e:
                click.echo(f"Clipboard copy failed: {e}", err=True)

    except SymlinkEncounteredError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConstraintViolatedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
