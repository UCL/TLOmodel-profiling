import os
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from utils import write_md_image


def make_stats_plots(data: pd.DataFrame, plot_output_dir: Path) -> Dict[str, Path]:
    """
    Using the data in the provided DataFrame, create and save plots of this
    information to the output directory.

    The DataFrame provided is intended to be the "site df" managed by the WebsiteBuilder.

    Return a dictionary whose keys are the names of the plots, and whose values are
    the paths to the images of those plots.
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


def markdown_for_run_plots(plot_dict: Dict[str, Path], build_dir: Path) -> List[str]:
    """
    Given a dictionary of plot names and the corresponding locations
    of the files that contain the plots, write markdown to include
    the plots as images.
    """
    markdown_string = ""
    for plot_name, location in plot_dict.items():
        markdown_string += f"\n### {plot_name} \n"
        markdown_string += write_md_image(location, build_dir, plot_name)

    return markdown_string
