"""convert_pyis
Wrapper functions for converting pyisession (pyis) files to HMTL and JSON.
"""
import os
from pathlib import Path
from typing import Literal

from pyinstrument.session import Session
from pyinstrument.renderers import HTMLRenderer, JSONRenderer


def convert_pyis(
    pyis_in: Path,
    output_file: Path,
    fmt: Literal["html", "json"] = "html",
    verbose: bool = True,
) -> None:
    """
    Converts a pyis session file to another file format for output parsing.

    :param pyis_in: The .pyisession file to convert.
    :param output_file: The Path to write the converted file to.
    :param fmt: The format to convert to; either 'html' or 'json'.
    :param verbose: If True, write to stdout the file name and its conversion.
    """
    pyi_session = Session.load(pyis_in)
    if not os.path.exists(output_file.parent):
        os.makedirs(output_file.parent)

    if fmt == "html":
        renderer = HTMLRenderer(show_all=False, timeline=False)
    elif fmt == "json":
        renderer = JSONRenderer(show_all=False, timeline=False)
    else:
        raise RuntimeError(f"pyis session cannot be converted to {fmt}")

    if verbose:
        print(f"Writing {output_file}", end="...", flush=True)
    with open(output_file, "w") as f:
        f.write(renderer.render(pyi_session))
    if verbose:
        print("done")
    return
