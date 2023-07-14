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


def pyis_to_html(pyis_in: Path, html_out: Path) -> None:
    """
    Renders a pyis session file as HTML for visual output.
    """
    convert_pyis(pyis_in, html_out, "html")
    return


def pyis_to_json(pyis_in: Path, json_out: Path):
    """
    Renders a pyis session file as JSON for reading profiling information into DataFrames.
    """
    convert_pyis(pyis_in, json_out, "json", verbose=False)
    return
