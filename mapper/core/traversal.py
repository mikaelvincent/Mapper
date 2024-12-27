"""
Logic for directory traversal and file reading in Mapper.
"""

import os

from mapper.core.defaults import DEFAULT_CONFIG

class SymlinkEncounteredError(Exception):
    pass

class ConstraintViolatedError(Exception):
    pass

def read_file_safely(path):
    """
    Return the contents of the file at 'path', or an empty string
    if the file does not exist or cannot be read.
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
        except (UnicodeDecodeError, OSError, LookupError):
            continue
    return ""

def build_directory_tree(
    current_path,
    prefix,
    lines,
    config,
    include_patterns,
    ignore_patterns,
    omit_patterns,
    file_count_tracker,
    determine_inclusion_status
):
    """
    Recursively traverse the directory structure, appending lines
    representing files and directories to 'lines'.
    Raises errors if symlinks are encountered or if file limits are exceeded.
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
        if os.path.islink(entry_path):
            raise SymlinkEncounteredError(f"Symlink found: {entry_path}")

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
                file_count_tracker=file_count_tracker,
                determine_inclusion_status=determine_inclusion_status
            )
        else:
            lines.append(f"{prefix}{connector} {entry}")
            file_count_tracker[0] += 1
            max_files = config.get("max_files")
            if max_files is not None and file_count_tracker[0] > max_files:
                raise ConstraintViolatedError(
                    f"File limit exceeded: more than {max_files} files found."
                )

            if is_omitted:
                if not config.get("minimal_output", False):
                    lines.append(f"{prefix}    [omitted]")
                continue

            if not config.get("minimal_output", False):
                file_content = read_file_with_encodings(entry_path, config)
                if config.get("trim_trailing_whitespaces", True):
                    file_content = "\n".join(
                        line.rstrip() for line in file_content.splitlines()
                    )
                if config.get("trim_all_empty_lines", False):
                    file_content = "\n".join(
                        line for line in file_content.splitlines() if line.strip() != ""
                    )
                max_chars = config.get("max_characters_per_file")
                if max_chars is not None and len(file_content) > max_chars:
                    raise ConstraintViolatedError(
                        f"Character limit exceeded in {entry} ({len(file_content)} chars)."
                    )
                if file_content:
                    for line in file_content.splitlines():
                        lines.append(f"{prefix}    {line}")
