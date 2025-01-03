"""
Tests for the traversal-related functionality in mapper.core.traversal.
"""

import os
import pytest
from mapper.core.traversal import (
    build_directory_tree,
    read_file_safely,
    SymlinkEncounteredError,
    ConstraintViolatedError
)
from mapper.core.filters import determine_inclusion_status
from mapper.core.defaults import DEFAULT_CONFIG

@pytest.mark.usefixtures("in_temp_dir")
def test_read_file_safely_non_existent():
    """
    Validate that read_file_safely returns an empty string if the file does not exist.
    """
    content = read_file_safely("no_such_file.txt")
    assert content == ""

@pytest.mark.usefixtures("in_temp_dir")
def test_read_file_safely_access_error():
    """
    Validate that read_file_safely handles an OSError gracefully.
    """
    file_name = "restricted_file.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("some content")
    try:
        os.chmod(file_name, 0o000)
    except PermissionError:
        pytest.skip("Skipping chmod test due to insufficient permissions.")

    content = read_file_safely(file_name)
    assert isinstance(content, str)

@pytest.mark.usefixtures("in_temp_dir")
def test_build_directory_tree_symlink_error():
    """
    Validate that build_directory_tree raises SymlinkEncounteredError when encountering a symlink.
    """
    os.mkdir("subfolder")
    config = dict(DEFAULT_CONFIG)
    file_count_tracker = [0]
    structure_lines = []
    file_contents_map = {}

    if hasattr(os, "symlink"):
        with open("file.txt", "w", encoding="utf-8") as f:
            f.write("dummy")
        os.symlink("file.txt", "subfolder/link_to_file")
    else:
        pytest.skip("Symlinks not supported on this platform.")

    with pytest.raises(SymlinkEncounteredError):
        build_directory_tree(
            current_path="subfolder",
            prefix="",
            structure_lines=structure_lines,
            file_contents_map=file_contents_map,
            config=config,
            include_patterns=[],
            ignore_patterns=[],
            omit_patterns=[],
            file_count_tracker=file_count_tracker,
            determine_inclusion_status=determine_inclusion_status
        )

@pytest.mark.usefixtures("in_temp_dir")
def test_build_directory_tree_exceed_file_limit():
    """
    Validate that build_directory_tree raises ConstraintViolatedError when file limit is exceeded.
    """
    os.mkdir("test_folder")
    config = dict(DEFAULT_CONFIG)
    config["max_files"] = 1
    file_count_tracker = [0]
    structure_lines = []
    file_contents_map = {}

    with open(os.path.join("test_folder", "file1.txt"), "w", encoding="utf-8") as f:
        f.write("content")
    with open(os.path.join("test_folder", "file2.txt"), "w", encoding="utf-8") as f:
        f.write("content")

    with pytest.raises(ConstraintViolatedError):
        build_directory_tree(
            current_path="test_folder",
            prefix="",
            structure_lines=structure_lines,
            file_contents_map=file_contents_map,
            config=config,
            include_patterns=[],
            ignore_patterns=[],
            omit_patterns=[],
            file_count_tracker=file_count_tracker,
            determine_inclusion_status=determine_inclusion_status
        )
