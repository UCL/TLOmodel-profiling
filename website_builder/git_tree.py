import os
import fnmatch
from pathlib import Path
from typing import List, Union

import git

from _paths import GIT_ROOT

REPO = git.Repo(GIT_ROOT)


def list_paths(root_tree, path: Path = Path(".")) -> List[Path]:
    """
    Return a generator that iterates over all files (with absolute paths)
    recursively, starting in the directory provided on the given tree.

    This method is recursive so should not be used on deep / tall tree structures.

    :param root_tree: Tree (branch/sub-branch/repository) to recurse through.
    :param path: The folder in which to begin recursing. Default is the root of the tree.
    :type path: Path, optional.
    :return: A list of Paths to the files that were found.
    :rtype: List[Path]
    """
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)


def branch_contents(branch_name: str, match_pattern: str = None) -> List[Path]:
    """
    List the contents of a given branch in the repository, optionally matching
    the pattern provided.

    :param branch_name: Name of a branch in the repository tree.
    :type branch_name: str
    :param match_pattern: Pattern to match in filenames.
    :type match_pattern: str, optional
    :return: List of Paths to the files on the branch that match the pattern.
    :rtype: List[Path]
    """
    try:
        branch_tree = getattr(REPO.heads, branch_name).commit.tree
    except AttributeError as e:
        raise RuntimeError(f"{branch_name} not found in the REPO") from e

    files = [str(file) for file in list_paths(branch_tree)]

    if match_pattern is not None:
        files = fnmatch.filter(files, match_pattern)

    files = [Path(file) for file in files]
    return files


def file_contents(branch_name: str, path_to_file: Path, write_to: Path = None) -> str:
    """
    Fetches the content of a file on another branch, returning it as a character string.

    If the write_to parameter is specified, contents will be dumped to the file location
    provided.

    :param branch_name: Name of a branch in the repository tree.
    :type branch_name: str
    :param path_to_file: Path to the file on the target branch to fetch.
    :type path_to_file: Path
    :param write_to: If provided, write the contents of the file to this location.
    :type write_to: Path, optional
    :returns: The content (as a string) of the requested file.
    :rtype: str
    """
    file_contents = REPO.git.show(f"{branch_name}:{str(path_to_file)}")

    if write_to is not None:
        if not os.path.exists(write_to.parent):
            os.makedirs(write_to.parent)
        with open(write_to, "w") as f:
            f.write(file_contents)
    return file_contents
