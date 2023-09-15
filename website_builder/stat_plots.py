import os
from pathlib import Path
from typing import Callable, Dict, List, Literal, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from additional_statistics import STATS
from utils import write_image_link


def make_stats_plots(
    data: pd.DataFrame, plot_output_dir: Path, plot_size: Tuple[int, int] = (12, 12)
) -> Tuple[Dict[str, Path], Dict[str, Path]]:
    """
    Using the data in the provided DataFrame, create and save plots of this
    information to the output directory.

    The DataFrame provided is intended to be the "site df" managed by the WebsiteBuilder.

    Return a dictionary whose keys are the names of the plots, and whose values are
    the paths to the images of those plots.

    :param data: Dataframe where each row corresponds to a pyis session, and the columns contain the statistics we are interested in recording.
    :param plot_output_dir: Directory to place any created plots into.
    :returns: Two dictionaries whose keys are the names of the graphical plots produced, and the values are the locations of the corresponding image files. The first corresponds to plots created from information from the
    pyisession files, and the second from the additional statistics.
    """
    # The plots that will be created
    plot_dict = {"CPU Time": plot_output_dir / "runtime_figure.svg"}

    # Create output directory if it doesn't exist
    if not os.path.exists(plot_output_dir):
        os.makedirs(plot_output_dir)

    # Create a plot of the profiling session runtime
    runtime_fig, runtime_ax = plt.subplots(figsize=plot_size)
    data.plot(x="Start Time", y="duration (s)", ax=runtime_ax)
    runtime_ax.set_xlabel("Run triggered on")
    runtime_ax.set_ylabel("Runtime (s)")
    runtime_ax.set_title("Profiling script CPU runtime")
    runtime_fig.tight_layout()
    runtime_fig.savefig(plot_dict["CPU Time"], bbox_inches=None)

    # Create plots for every Statistic that we want to record
    stat_dict = dict()
    if not STATS.is_empty():
        for s in STATS.statistics:
            # check that there is numeric data to plot!
            if data[s.dataframe_col_name].first_valid_index() is not None:
                # Create and save plot
                fig, ax = plt.subplots(figsize=plot_size)
                data.plot(x="Start Time", y=s.dataframe_col_name, ax=ax)
                ax.set_xlabel("Run triggered on")
                ax.set_ylabel(s.plot_y_label)
                ax.set_title(s.plot_title)
                fig.tight_layout()
                fig.savefig(plot_output_dir / s.plot_svg_name, bbox_inches=None)
                # Update dictionary that is tracking the plots we produce
                stat_dict[s.plot_title] = plot_output_dir / s.plot_svg_name

    # Create any other plots you might want
    return plot_dict, stat_dict


def write_string_for_run_plots(
    pyis_dict: Dict[str, Path],
    stat_dict: Dict[str, Path],
    relative_to: Path = None,
    format: Literal["rst", "md"] = "rst",
) -> List[str]:
    """
    Given a dictionary of plot names and the corresponding locations
    of the files that contain the plots, write a string that can be
    written to a file to include the plots as images.

    The text string that is produced can either be in markdown (md)
    or restructured text (rst) format.

    :param plot_dict, stat_dict: Dictionary whose keys are the names of plots, and whose values are the locations of the image files containing the plots. The former is for plots using data extracted from the pyisession files, the
    latter for data from the additional statistics files.
    :param relative_to: Links to plots will be written relative to this directory, if provided.
    :param dir_containing_plots: Path to the folder where the plots are located.
    :param format: The text format of the output string; 'md' (markdown) or 'rst' (restructured text).
    :returns: A text string containing includes for each of the images provided.
    """
    pre_link: Callable[[str], str]
    # Link format depends on whether we are writing rst or md
    if format == "rst":
        pre_link = lambda title_text: rst_title_format(title_text, "-")
    elif format == "md":
        pre_link = md_title_format
    else:
        raise ValueError(f"{format} is not markdown (md) or restructured text (rst).")

    string = ""
    for plot_collection in [pyis_dict, stat_dict]:
        for plot_name, location in plot_collection.items():
            string += pre_link(plot_name)
            string += write_image_link(location, relative_to, plot_name, format)
            string += "\n"

    return string


def rst_title_format(title_text: str, undercharacter: str = "-") -> str:
    return f"\n{title_text}\n" + (undercharacter * len(title_text)) + ("\n" * 2)


def md_title_format(title_text: str) -> str:
    return f"\n### {title_text}\n"
