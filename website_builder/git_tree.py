import os
import fnmatch
from pathlib import Path
from typing import List, Union

import git

from _paths import GIT_ROOT

REPO = git.Repo(GIT_ROOT)


def list_paths(root_tree, path=Path(".")) -> List[Path]:
    """
    Return a generator that iterates over all files (with absolute paths)
    recursively, starting in the directory provided on the given tree.

    :param root_tree: Tree (branch/sub-branch/repository) to recurse through.
    :param path: The folder in which to begin recursing.
    :return: A list of Paths to the files that were found.
    """
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)


def branch_contents(branch_name: str, match_pattern: str = None) -> List[Path]:
    """
    List all contents of a given branch in the repository, which match
    the UNIX pattern provided.

    :param branch_name: Name of a branch in the repository tree.
    :param match_pattern: Pattern to match in filenames.
    :return: List of Paths to the files on the branch that match the pattern.
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


def file_contents(
    branch_name: str, path_to_file: Union[str, Path], write_to: Union[str, Path] = None
) -> str:
    """
    Fetches the content of a file on another branch, and returns them as a string.

    Contents can be dumped to a file by specifying write_to.

    :param branch_name: Name of a branch in the repository.
    :param path_to_file: Path to the file on the target branch to fetch.
    :param write_to: If provided, write the contents of the file to this location.
    :returns: The content (as a string) of the requested file.
    """
    file_contents = REPO.git.show(f"{branch_name}:{str(path_to_file)}")

    if write_to is not None:
        if not os.path.exists(write_to.parent):
            os.makedirs(write_to.parent)
        with open(write_to, "w") as f:
            f.write(file_contents)
    return file_contents
