from pathlib import Path
from typing import Tuple

from git_tree import REPO

# Filenames are assumed to have the format
# path/to/file/{GH_EVENT}_{GH_ID}_{GH_SHA}.extension
# Assuming this convention, we can extract the individual pieces of information
# from the filename.


def git_SHA(fname: Path) -> Tuple[str, str]:
    """
    Extract the git commit SHA and hash, given an pyis session file.
    """
    sha = fname.stem.split("_")[-1]
    hash = REPO.git.rev_parse("--short", sha)
    return sha, hash


def git_event(fname: Path) -> str:
    """
    Extract the name of the git event that triggered the profiling run.

    workflow_dispatch events introduce a spurious underscore,
    so we catch those cases.
    """
    split_name = fname.stem.split("_")
    if split_name[0] != "workflow":
        return split_name[0]
    else:
        return "workflow dispatch"
