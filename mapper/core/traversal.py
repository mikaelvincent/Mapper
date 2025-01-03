import os

from mapper.core.defaults import DEFAULT_CONFIG

class SymlinkEncounteredError(Exception):
    pass

class ConstraintViolatedError(Exception):
    pass

class EncodingDetectionError(Exception):
    """
    Raised when automatic encoding detection fails or is inconclusive.
    """
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

def read_file_with_encoding_detection(path, config):
    """
    Detect encoding using an external library or apply force_encoding if set.
    Raise EncodingDetectionError if detection fails.
    """
    if not os.path.isfile(path):
        return ""

    # If the user has explicitly forced a particular encoding, use it directly.
    forced_enc = config.get("force_encoding")
    if forced_enc:
        try:
            with open(path, "r", encoding=forced_enc) as f:
                return f.read()
        except (UnicodeDecodeError, OSError, LookupError):
            raise EncodingDetectionError(
                f"Failed to decode {path} using forced encoding: {forced_enc}"
            )

    # Automatic detection if force_encoding is None.
    import chardet
    try:
        with open(path, "rb") as f:
            raw_data = f.read()
        detection_result = chardet.detect(raw_data)
        detected_enc = detection_result.get("encoding")
        confidence = detection_result.get("confidence", 0)

        if not detected_enc or confidence < 0.5:
            raise EncodingDetectionError(
                f"Encoding detection failed or confidence too low for {path}."
            )

        return raw_data.decode(detected_enc, errors="strict")

    except (UnicodeDecodeError, OSError):
        raise EncodingDetectionError(
            f"Failed to decode {path} with detected encoding: {detected_enc}"
        )

def build_directory_tree(
    current_path,
    prefix,
    structure_lines,
    file_contents_map,
    config,
    include_patterns,
    ignore_patterns,
    omit_patterns,
    file_count_tracker,
    determine_inclusion_status
):
    """
    Recursively traverse the directory structure, appending lines
    to 'structure_lines' and populating 'file_contents_map' with
    file content keyed by relative path.

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
            continue

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
            structure_lines.append(f"{prefix}{connector} {entry}")
            build_directory_tree(
                current_path=entry_path,
                prefix=new_prefix,
                structure_lines=structure_lines,
                file_contents_map=file_contents_map,
                config=config,
                include_patterns=include_patterns,
                ignore_patterns=ignore_patterns,
                omit_patterns=omit_patterns,
                file_count_tracker=file_count_tracker,
                determine_inclusion_status=determine_inclusion_status
            )
        else:
            structure_lines.append(f"{prefix}{connector} {entry}")
            file_count_tracker[0] += 1
            max_files = config.get("max_files")
            if max_files is not None and file_count_tracker[0] > max_files:
                raise ConstraintViolatedError(
                    f"File limit exceeded: more than {max_files} files found."
                )

            if is_omitted:
                file_contents_map[relative_entry_path] = "[omitted]"
                continue

            if not config.get("minimal_output", False):
                try:
                    file_content = read_file_with_encoding_detection(entry_path, config)
                except EncodingDetectionError as e:
                    # Abort if detection fails
                    raise ConstraintViolatedError(str(e))

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

                file_contents_map[relative_entry_path] = file_content
            else:
                file_contents_map[relative_entry_path] = ""
