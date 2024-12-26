"""
Filtering logic for .mapignore, .mapomit, and .mapinclude.
Uses a .gitignore-like syntax and respects the priority:
1) .mapinclude > 2) .mapignore > 3) .mapomit.
"""

import fnmatch
import os

def parse_pattern_file(file_path):
    """
    Parse a file containing patterns (e.g., .mapignore) that follow
    a .gitignore-like syntax, ignoring empty or commented lines.

    Returns a list of patterns.
    """
    patterns = []
    if not os.path.isfile(file_path):
        return patterns

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns

def is_match(path, patterns):
    """
    Determine whether the given path matches any pattern in the
    provided list of patterns. This relies on fnmatch.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def determine_inclusion_status(
    path,
    include_patterns,
    ignore_patterns,
    omit_patterns
):
    """
    Determine whether a file or directory should be included, ignored,
    or omitted based on patterns from .mapinclude, .mapignore, and .mapomit.

    Returns:
    (bool should_include, bool is_omitted)

    - should_include: True if the path is included in the final output,
      False if it is excluded entirely.
    - is_omitted: True if the path is included but its content should be
      replaced by [omitted].
    """
    # If .mapinclude has entries, only those matching its patterns are considered.
    if include_patterns:
        if not is_match(path, include_patterns):
            return False, False

    # Next, apply .mapignore (if matched, exclude entirely).
    if is_match(path, ignore_patterns):
        return False, False

    # Finally, apply .mapomit (if matched, content is omitted).
    if is_match(path, omit_patterns):
        return True, True

    # If none of the above patterns apply, include normally.
    return True, False
