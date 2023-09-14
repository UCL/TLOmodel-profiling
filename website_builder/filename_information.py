from pathlib import Path
from typing import Tuple

from git_tree import REPO


def git_info_from_filename(fname: Path) -> Tuple[str, str, str]:
    """
    Extract git information (event, sha, and hash) from the filename provided.

    Filenames are assumed to have the format
        path/to/file/{GH_EVENT}_{GH_ID}_{GH_SHA}.extension
    Assuming this convention, we can extract the individual pieces of information
    from the filename.

    :param fname: File name in the assumed format.
    :returns: The event, sha, and hash values as strings, in that order.
    """
    split_name = fname.stem.split("_")
    if split_name[0] != "workflow":
        event = split_name[0].upper()
    else:
        event = "workflow dispatch".upper()
    sha = split_name[-1]
    hash = REPO.git.rev_parse("--short", sha)
    return event, sha, hash
