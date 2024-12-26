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

    # Gather patterns from .mapinclude, .mapignore, and .mapomit
    include_patterns = parse_pattern_file(".mapinclude")
    # If .mapinclude is empty, ignore it
    if not include_patterns:
        include_patterns = []
    ignore_patterns = parse_pattern_file(".mapignore")
    omit_patterns = parse_pattern_file(".mapomit")

    # Read .mapheader and .mapfooter if present
    mapheader_content = read_file_safely(".mapheader")
    mapfooter_content = read_file_safely(".mapfooter")

    # Perform directory traversal
    try:
        content_lines = []
        # If use_absolute_path_title is True, use absolute path
        if config.get("use_absolute_path_title", False):
            top_label = os.path.abspath(os.getcwd())
        else:
            top_label = os.path.basename(os.getcwd()) or os.getcwd()

        content_lines.append(top_label)
        content_lines.append("")  # Spacing line

        tree_lines = []
        file_count_tracker = [0]  # Use a list for mutable integer
        build_directory_tree(
            current_path=".",
            prefix="",
            lines=tree_lines,
            config=config,
            include_patterns=include_patterns,
            ignore_patterns=ignore_patterns,
            omit_patterns=omit_patterns,
            file_count_tracker=file_count_tracker
        )

        content_lines.extend(tree_lines)

        # Construct final output
        final_output = []
        if mapheader_content:
            final_output.append(mapheader_content.strip() + "\n")

        final_output.append("\n".join(content_lines))

        if mapfooter_content:
            final_output.append("\n---\n" + mapfooter_content.strip() + "\n")

        rendered_output = "\n".join(final_output)

        # Write to output file unless constraints have already halted
        # If constraints are violated, an exception is raised in build_directory_tree
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_output + "\n")

        # Copy to clipboard if requested
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


def build_directory_tree(
    current_path,
    prefix,
    lines,
    config,
    include_patterns,
    ignore_patterns,
    omit_patterns,
    file_count_tracker
):
    """
    Recursively traverse the directory structure, appending lines
    representing files and directories to 'lines'.
    Raise errors if symlinks are encountered or if file limits are exceeded.
    """
    entries = sorted(os.listdir(current_path))
    for i, entry in enumerate(entries):
        if entry in (
            ".mapheader",
            ".mapfooter",
            ".mapignore",
            ".mapomit",
            ".mapinclude",
            ".mapconfig"
        ):
            # Exclude mapper-related files
            continue

        # Hidden file check
        if config.get("ignore_hidden", True) and entry.startswith("."):
            continue

        entry_path = os.path.join(current_path, entry)
        # Check for symlinks
        if os.path.islink(entry_path):
            raise SymlinkEncounteredError(f"Symlink found: {entry_path}")

        # Determine whether entry is included, ignored, or omitted
        relative_entry_path = entry_path.lstrip("./\\")
        should_include, is_omitted = determine_inclusion_status(
            relative_entry_path,
            include_patterns,
            ignore_patterns,
            omit_patterns
        )
        if not should_include:
            continue

        connector = "├──" if i < len(entries) - 1 else "└──"
        new_prefix = prefix + ("│   " if i < len(entries) - 1 else "    ")

        if os.path.isdir(entry_path):
            lines.append(f"{prefix}{connector} {entry}")
            build_directory_tree(
                current_path=entry_path,
                prefix=new_prefix,
                lines=lines,
                config=config,
                include_patterns=include_patterns,
                ignore_patterns=ignore_patterns,
                omit_patterns=omit_patterns,
                file_count_tracker=file_count_tracker
            )
        else:
            # It's a file
            lines.append(f"{prefix}{connector} {entry}")

            # Update file count
            file_count_tracker[0] += 1
            max_files = config.get("max_files")
            if max_files is not None and file_count_tracker[0] > max_files:
                raise ConstraintViolatedError(
                    f"File limit exceeded: more than {max_files} files found."
                )

            # If omitted, skip content reading
            if is_omitted:
                # The specification only shows [omitted] in .map
                # For minimal_output, do not add content lines
                if not config.get("minimal_output", False):
                    lines.append(f"{prefix}    [omitted]")
                continue

            # Read file contents if needed
            if not config.get("minimal_output", False):
                file_content = read_file_with_encodings(entry_path, config)
                # Trim trailing whitespaces
                if config.get("trim_trailing_whitespaces", True):
                    file_content = "\n".join(line.rstrip() for line in file_content.splitlines())
                # Remove empty lines entirely if specified
                if config.get("trim_all_empty_lines", False):
                    file_content = "\n".join(line for line in file_content.splitlines() if line.strip() != "")

                # Check for max_characters_per_file
                max_chars = config.get("max_characters_per_file")
                if max_chars is not None and len(file_content) > max_chars:
                    raise ConstraintViolatedError(
                        f"Character limit exceeded in {entry} ({len(file_content)} chars)."
                    )

                if file_content:
                    for line in file_content.splitlines():
                        lines.append(f"{prefix}    {line}")


def read_file_safely(path):
    """
    Return the contents of the file at 'path', or an empty string
    if the file does not exist.
    """
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def read_file_with_encodings(path, config):
    """
    Attempt to read a file with the encodings specified in config['encodings'],
    falling back on defaults if reading fails.
    """
    encodings_list = config.get("encodings", DEFAULT_CONFIG["encodings"])
    for enc in encodings_list:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, OSError):
            continue
    return ""


class SymlinkEncounteredError(Exception):
    pass


class ConstraintViolatedError(Exception):
    pass
