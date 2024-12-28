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

    Folder structure is listed first, followed by file contents, each
    separated by triple dashes.
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

    use_spacing = not config.get("minimal_output", False)

    try:
        structure_lines = []
        file_contents_map = {}
        if config.get("use_absolute_path_title", False):
            top_label = os.path.abspath(os.getcwd())
        else:
            top_label = os.path.basename(os.getcwd()) or os.getcwd()

        structure_lines.append(top_label)
        structure_lines.append("")

        file_count_tracker = [0]
        build_directory_tree(
            current_path=".",
            prefix="",
            structure_lines=structure_lines,
            file_contents_map=file_contents_map,
            config=config,
            include_patterns=include_patterns,
            ignore_patterns=ignore_patterns,
            omit_patterns=omit_patterns,
            file_count_tracker=file_count_tracker,
            determine_inclusion_status=determine_inclusion_status
        )

        final_output = []

        # If .mapheader exists, add its content, then optional spacing, then a triple dash, and optional spacing again.
        if mapheader_content:
            final_output.append(mapheader_content.strip())
            if use_spacing:
                final_output.append("")
            final_output.append("---")
            if use_spacing:
                final_output.append("")

        # Add the folder structure, then optional spacing, then a triple dash, and optional spacing again.
        final_output.append("\n".join(structure_lines))
        if use_spacing:
            final_output.append("")
        final_output.append("---")
        if use_spacing:
            final_output.append("")

        # Append file contents, each wrapped in triple backticks and separated by triple dashes.
        file_paths = list(file_contents_map.keys())
        for idx, path in enumerate(file_paths):
            # By default, add a colon and a line break after the file name unless minimal_output is True.
            if use_spacing:
                final_output.append(f"{path}:")
                final_output.append("")
            else:
                final_output.append(path)

            content = file_contents_map[path]
            if content:
                final_output.append("```")
                final_output.append(content)
                final_output.append("```")

            if idx < len(file_paths) - 1:
                if use_spacing:
                    final_output.append("")
                final_output.append("---")
                if use_spacing:
                    final_output.append("")
            else:
                # Transition from the last file content to the footer, if present.
                if mapfooter_content:
                    if use_spacing:
                        final_output.append("")
                    final_output.append("---")
                    if use_spacing:
                        final_output.append("")

        # Finally, if .mapfooter exists, add its content.
        if mapfooter_content:
            final_output.append(mapfooter_content.strip())

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
