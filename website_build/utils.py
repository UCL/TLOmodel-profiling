from datetime import datetime
import fileinput
import os
from pathlib import Path
import shutil

from _paths import DEFAULT_BUILD_DIR, GIT_ROOT


def create_dump_folder(build_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    """
    Creates a temporary folder within the build directory that can be used to
    dump temporary files, then removed once the build process is over.
    """
    dump_folder = (build_dir / datetime.utcnow().strftime("%Y%m%d%H%M_tmp")).resolve()
    if os.path.exists(dump_folder):
        raise RuntimeError(f"Temporary directory {dump_folder} already exists!")
    else:
        os.makedirs(dump_folder)
    return dump_folder


def clean_build_directory(build_dir: Path) -> None:
    """
    Remove the build directory and any files within in.
    Only works when the build directory is within the repository root.
    """
    if GIT_ROOT not in build_dir.parents:
        raise RuntimeError(
            f"Cannot remove build directory {build_dir} as it is outside repository root {GIT_ROOT}, so could be harmful. Please manually clear the build directory."
        )
    elif os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    return


def write_md_image(
    link: Path, relative_to: Path = None, alt_text: str = "IMAGE"
) -> str:
    """
    Create a markdown image embedding of the form
    ![alt_text](image_source)

    where image_source points to the file at link relative to the relative_to path.
    """
    if relative_to is not None:
        image_source = os.path.relpath(link, relative_to)
    else:
        image_source = str(link)
    return f"![{alt_text}]({image_source})"


def write_md_link(link: Path, relative_to: Path = None, link_text: str = "LINK") -> str:
    """
    Create a markdown hyperlink of the form
    [link_text](HyperLink)

    where the HyperLink points to the file link relative to the relative_to path.
    """
    if relative_to is not None:
        hyperlink = os.path.relpath(link, relative_to)
    else:
        hyperlink = str(link)
    return f"[{link_text}]({hyperlink})"


def write_rst_link(
    link: Path, relative_to: Path = None, link_text: str = "LINK"
) -> str:
    """
    Create an rst external-file hyperlink of the form
    `link_text <hyperlink>`_

    where the hyperlink points to the file link relative to relative_to path.
    """
    if relative_to is not None:
        hyperlink = os.path.relpath(link, relative_to)
    else:
        hyperlink = str(link)
    return f"`{link_text} <{hyperlink}>`_"


def write_rst_image(link: Path, relative_to: Path = None) -> str:
    """
    Create a rst image embedding of the form
    ..image:: image_source

    where image_source points to the file at link relative to the relative_to path.
    """
    if relative_to is not None:
        image_source = os.path.relpath(link, relative_to)
    else:
        image_source = str(link)
    return f"..image:: {image_source}"


def replace_in_file(file: Path, search_for: str, replace_with: str) -> None:
    """
    Replace all occurrences of the (sub)string search_for in the file with the replace_with string.
    """
    with fileinput.FileInput(file, inplace=True) as f:
        for line in f:
            print(line.replace(search_for, replace_with), end="")
    return
