from datetime import datetime
import fileinput
import os
from pathlib import Path
import shutil
from typing import Literal

from _paths import GIT_ROOT


def md_title_format(title_text: str) -> str:
    """
    Returns the string provided as a MarkDown title.
    """
    return f"\n### {title_text}\n"


def replace_in_file(file: Path, search_for: str, replace_with: str) -> None:
    """
    Replace all occurrences of a string in a file with another.

    Operation is performed in-place - original file will be modified.

    :param file: Path to file to operate on.
    :param search_for: String pattern to match.
    :param replace_with: String to replace the matched pattern with.
    """
    with fileinput.FileInput(file, inplace=True) as f:
        for line in f:
            print(line.replace(search_for, replace_with), end="")
    return


def rst_title_format(title_text: str, undercharacter: str = "-") -> str:
    """
    Returns the string provided as a ReStructured text title,
    using the undercharacter to denote the depth/level of the title.
    """
    return f"\n{title_text}\n" + (undercharacter * len(title_text)) + ("\n" * 2)


def safe_remove_dir(dir: Path) -> None:
    """
    Remove the directory and any files within in.
    Only works when the directory provided is within the repository root,
    raises a RuntimeError if this is not the case.

    :param dir: Path to the directory to remove, along with its contents.
    """
    if GIT_ROOT not in dir.parents:
        raise RuntimeError(
            f"Cannot remove build directory {dir} as it is outside repository root {GIT_ROOT}, so could be harmful. Please manually clear the build directory."
        )
    elif os.path.exists(dir):
        shutil.rmtree(dir)
    return


def timestamp_to_time(timestamp: float) -> str:
    """
    Convert a timestamp (float representing a number of seconds from a reference date)
    into a human-readable date-time format.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d, %H:%M:%S")


def write_image_link(
    link: Path,
    relative_to: Path = None,
    alt_text: str = "IMAGE",
    format: Literal["md", "rst"] = "rst",
) -> str:
    """
    Write a string that encodes a link to an image, in either
    markdown (md) or restructured text  (rst) format.

    For .rst format, the output string has the form:
    ..image:: image_source
       :alt: alt_text

    For .md (markdown) format, the output string has the form:
    ![alt_text](image_source)

    :param link: Path to the image file to include.
    :param relative_to: If provided, the image_source link will be provided relative to this location.
    :param alt_text: Alternate text to display when image cannot be rendered in a browser.
    :param format: The format of the output string; 'rst' (restructured text) or 'md' (markdown).
    :param format: The string encoding the link to the image.
    """
    if relative_to is not None:
        image_source = os.path.relpath(link, relative_to)
    else:
        image_source = str(link)
    if format == "rst":
        string = f".. image:: {image_source}"
        string += "\n" + (" " * 3) + f":alt: {alt_text}"
    elif format == "md":
        string = f"![{alt_text}]({image_source})"
    else:
        raise ValueError(f"{format} is not markdown (md) or restructured text (rst).")
    return string


def write_page_link(
    link: Path,
    relative_to: Path = None,
    link_text: str = "LINK",
    format: Literal["rst", "md"] = "rst",
) -> str:
    """
    Write a string that encodes a link to another page, in either
    markdown (md) or restructured text  (rst) format.

    For .rst format, the output string has the form:
    `link_text <hyperlink>`

    For .md (markdown) format, the output string has the form:
    [link_text](hyperlink)

    If the link provided is NoneType, return an empty string.

    :param link: Path to the image file to include.
    :param relative_to: If provided, the hyperlink will be provided relative to this location.
    :param alt_text: Alternate text to display for the hyperlink.
    :param format: The format of the output string; 'rst' (restructured text) or 'md' (markdown).
    :param format: The string encoding the link to the page.
    :returns: String containing a link to the file.
    """
    if link is None:
        return "No data available"
    elif relative_to is not None:
        hyperlink = os.path.relpath(link, relative_to)
    else:
        hyperlink = str(link)
    if format == "rst":
        return f"`{link_text} <{hyperlink}>`__"
    elif format == "md":
        return f"[{link_text}]({hyperlink})"
    else:
        raise ValueError(f"{format} is not markdown (md) or restructured text (rst).")
