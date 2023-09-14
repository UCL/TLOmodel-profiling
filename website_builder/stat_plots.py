import os
from pathlib import Path
from typing import Dict, List, Literal

import matplotlib.pyplot as plt
import pandas as pd

from utils import write_image_link


def make_stats_plots(data: pd.DataFrame, plot_output_dir: Path) -> Dict[str, Path]:
    """
    Using the data in the provided DataFrame, create and save plots of this
    information to the output directory.

    The DataFrame provided is intended to be the "site df" managed by the WebsiteBuilder.

    Return a dictionary whose keys are the names of the plots, and whose values are
    the paths to the images of those plots.

    :param data: Dataframe where each row corresponds to a pyis session, and the columns contain the statistics we are interested in recording.
    :param plot_output_dir: Directory to place any created plots into.
    :returns: A dictionary whose keys are the names of the graphical plots produced, and the values are the locations of the corresponding image files.
    """
    # The plots that will be created
    plot_dict = {"CPU Time": plot_output_dir / "runtime_figure.svg"}

    # Create output directory if it doesn't exist
    if not os.path.exists(plot_output_dir):
        os.makedirs(plot_output_dir)

    # Create a plot or the profiling session runtime
    runtime_fig, runtime_ax = plt.subplots(figsize=(12, 12))
    data.plot(x="Start Time", y="duration (s)", ax=runtime_ax)
    runtime_ax.set_xlabel("Run triggered on")
    runtime_ax.set_ylabel("Runtime (s)")
    runtime_ax.set_title("Profiling script CPU runtime")
    runtime_fig.tight_layout()
    runtime_fig.savefig(plot_dict["CPU Time"], bbox_inches=None)

    # Create any other plots you might want
    return plot_dict


def write_string_for_run_plots(
    plot_dict: Dict[str, Path],
    relative_to: Path = None,
    format: Literal["rst", "md"] = "rst",
) -> List[str]:
    """
    Given a dictionary of plot names and the corresponding locations
    of the files that contain the plots, write a string that can be
    written to a file to include the plots as images.

    The text string that is produced can either be in markdown (md)
    or restructured text (rst) format.

    :param plot_dict: Dictionary whose keys are the names of plots, and whose values are the locations of the image files containing the plots.
    :param relative_to: Links to plots will be written relative to this directory, if provided.
    :param format: The text format of the output string; 'md' (markdown) or 'rst' (restructured text).
    :returns: A text string containing includes for each of the images provided.
    """
    # Link format depends on whether we are writing rst or md
    if format == "rst":
        pre_link = rst_title_format
    elif format == "md":
        pre_link = md_title_format
    else:
        raise ValueError(f"{format} is not markdown (md) or restructured text (rst).")

    string = ""
    for plot_name, location in plot_dict.items():
        string += pre_link(plot_name)
        string += write_image_link(location, relative_to, plot_name, format)
        string += "\n"

    return string


def rst_title_format(title_text: str, undercharacter: str = "-") -> str:
    return f"\n{title_text}\n" + (undercharacter * len(title_text)) + ("\n" * 2)


def md_title_format(title_text: str) -> str:
    return f"\n### {title_text}\n"
