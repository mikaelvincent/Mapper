import os
import pytest
from mapper.core.filters import (
    parse_pattern_file,
    determine_inclusion_status,
    is_match
)

@pytest.fixture
def setup_test_files(tmp_path):
    """
    Creates temporary files for .mapignore, .mapomit, and .mapinclude testing.
    Returns a dictionary of file paths.
    """
    files = {
        "ignore": tmp_path / ".mapignore",
        "omit": tmp_path / ".mapomit",
        "include": tmp_path / ".mapinclude",
    }

    files["ignore"].write_text("# Comment line\n*.log\nsecret*", encoding="utf-8")
    files["omit"].write_text("# Another comment\n*.md\n", encoding="utf-8")
    files["include"].write_text("# .mapinclude\n", encoding="utf-8")

    return files

@pytest.mark.usefixtures("in_temp_dir")
def test_parse_pattern_file(setup_test_files):
    """
    Validate that parse_pattern_file correctly reads patterns and ignores comments.
    """
    ignore_file = setup_test_files["ignore"]
    patterns = parse_pattern_file(ignore_file)
    assert "*.log" in patterns
    assert "secret*" in patterns
    assert "# Comment line" not in patterns

@pytest.mark.usefixtures("in_temp_dir")
def test_is_match_function():
    """
    Validate that is_match correctly detects fnmatch patterns.
    """
    patterns = ["*.py", "docs/*", "folder[0-9]"]
    assert is_match("main.py", patterns) is True
    assert is_match("docs/index.html", patterns) is True
    assert is_match("folder1", patterns) is True
    assert is_match("image.jpg", patterns) is False

@pytest.mark.usefixtures("in_temp_dir")
def test_determine_inclusion_no_include(setup_test_files):
    """
    If .mapinclude is empty or contains no valid patterns, then .mapignore and
    .mapomit alone determine the outcome.
    """
    include_patterns = []  # Emulate empty .mapinclude
    ignore_patterns = ["*.log", "secret*"]
    omit_patterns = ["*.md"]

    # Excluded by ignore
    assert determine_inclusion_status("error.log", include_patterns, ignore_patterns, omit_patterns) == (False, False)
    # Omitted by omit
    assert determine_inclusion_status("README.md", include_patterns, ignore_patterns, omit_patterns) == (True, True)
    # Neither ignored nor omitted
    assert determine_inclusion_status("main.py", include_patterns, ignore_patterns, omit_patterns) == (True, False)

@pytest.mark.usefixtures("in_temp_dir")
def test_determine_inclusion_with_include():
    """
    If .mapinclude has valid entries, only those patterns are considered first.
    """
    include_patterns = ["*.py"]
    ignore_patterns = ["*.log", "secret*"]
    omit_patterns = ["*.md"]

    # Must match include to be considered
    assert determine_inclusion_status("main.py", include_patterns, ignore_patterns, omit_patterns) == (True, False)
    # Not in include, so excluded regardless of ignore/omit
    assert determine_inclusion_status("README.md", include_patterns, ignore_patterns, omit_patterns) == (False, False)
    # Not in include, so excluded
    assert determine_inclusion_status("error.log", include_patterns, ignore_patterns, omit_patterns) == (False, False)

@pytest.mark.usefixtures("in_temp_dir")
def test_priority_order():
    """
    Validate that .mapinclude overrides .mapignore, which overrides .mapomit.
    """
    include_patterns = ["secret.txt"]
    ignore_patterns = ["secret*"]
    omit_patterns = ["secret.txt"]

    should_include, is_omitted = determine_inclusion_status("secret.txt", include_patterns, ignore_patterns, omit_patterns)
    assert should_include is True
    assert is_omitted is False

    should_include, is_omitted = determine_inclusion_status("secret_config.yaml", include_patterns, ignore_patterns, omit_patterns)
    assert should_include is False
    assert is_omitted is False
