import argparse
from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
from subprocess import check_call
from typing import Callable, ClassVar, Dict, List, Literal, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from _paths import DEFAULT_BUILD_DIR, GIT_ROOT, SRC_DIR
from additional_statistics import STATS
from git_tree import REPO, branch_contents, file_contents
from stat_plots import md_title_format, rst_title_format
from utils import safe_remove_dir, replace_in_file, write_image_link, write_page_link

DESCRIPTION = (
    "Build the website deployment for the profiling results, "
    "placing the resulting files in the build directory."
)
# This pattern, where it appears in the template files,
# will be replaced with the profiling runs lookup table.
PROFILING_TABLE_MATCH_STRING = "<<<MATCH_PATTERN_FOR_MARKDOWN_TABLE_INSERT>>>"
# This pattern, where it appears in the template files,
# will be replaced with the plots for statistics that are tracked across runs
RUN_PLOTS_MATCH_STRING = "<<<MATCH_PATTERN_FOR_RUN_STATS_PLOTS>>>"

# These columns need to be computed from the statistics that are read in
# from the statistics files on the source branch
DF_EXTRA_COLUMNS = [
    "HTML",
    "Link",
    "Commit",
    "location_on_source_branch",
]
# These are all the column names that will be included in the DataFrame that
# manages building of the website.
DF_COLS = (
    {"stats_file"} | set(DF_EXTRA_COLUMNS) | set(STATS.values("dataframe_col_name"))
)


@dataclass
class WebsiteBuilder:
    """
    Handles the construction of the gh-pages website, as per the process detailed
    in http://github-pages.ucl.ac.uk/TLOmodel-profiling/repo-overview.html.

    Build options are configured on initialisation of a class instance;
    members with default values can be passed as keyword arguments to overwrite
    this default behaviour.

    Use the .build() method to run the website build.
    """

    # The git branch which holds the profiling results
    source_branch: str
    # The directory to build the website in
    build_dir: str

    # If True, static HTML files generated from profiling session outputs will be
    # placed into the profiling_html_dir in a flat structure.
    # If False, they will retain the YYYY/MM/DD/{name}.html structure of the
    # source branch.
    flatten_profiling_html: bool = True
    # If True, the build directory will be purged before starting
    # a new build.
    clean_build: bool = True
    # Folder containing website source and template files
    web_source_dir: Path = SRC_DIR
    # The file extension of the statistics files on the source branch
    stats_file_ext: str = "stats.json"
    # Whether the website templates to be edited are MarkDown (md)
    # or ReStructured Text (rst)
    website_plaintext_format: Literal["md", "rst"] = "rst"
    # The figure size to set for all plots that will be produced
    size_of_plots: Tuple[int, int] = (12, 6)
    # The columns from the website DataFrame to include in the profiling runs lookup table
    # The columns will be ordered as provided in the list.
    cols_for_lookup_table: List[str] = field(
        default_factory=lambda: [
            "Start time",
            "Link",
            "Commit",
            "Triggered by",
        ]
    )

    @property
    def staging_dir(self) -> Path:
        """
        The intermediate folder that sphinx-build will use as its source for building the website.
        This folder will contain static files that have to be generated from the results stored
        on the source branch; such as:
        * Static HTML files from profiling runs,
        * The rst files with the lookup tables inserted,
        * The run-statistics plots.
        """
        return Path(str(self.build_dir) + "-pre-build")

    @property
    def static_folder(self) -> Path:
        """
        The folder containing static html files that are to be linked to.
        """
        return self.staging_dir / "_static"

    @property
    def profiling_table_file(self) -> Path:
        """
        The file containing the
        <<<MATCH_PATTERN_FOR_MARKDOWN_TABLE_INSERT>>>,

        which is where the profiling results lookup table will be inserted.
        """
        return self.staging_dir / "profiling.rst"

    @property
    def statistics_plots_file(self) -> Path:
        """
        The file containing the
        <<<MATCH_PATTERN_FOR_RUN_STATS_PLOTS>>>,

        which is where the run statistics plots will be inserted.
        """
        return self.staging_dir / "run-statistics.rst"

    @property
    def plot_folder(self) -> Path:
        """
        The folder within the build directory that will contain any plots
        that are generated from the statistics collected across the profiling runs.
        """
        return self.static_folder / "plots"

    @property
    def profiling_html_dir(self) -> Path:
        """
        The folder within the build directory that will contain any HTML files
        generated from profiling sessions.
        """
        return self.static_folder / "profiling_html"

    # DataFrame whose rows correspond to profiling runs, and whose columns
    # contain the data collected from that profiling run.
    df: ClassVar[pd.DataFrame]
    # Dictionary whose key: value pairs match generated plots against
    # the name/title of the statistic that the plot displays
    plot_dict: ClassVar[Dict[str, str]]

    def __post_init__(self) -> None:
        """
        After instantiation, check for possible value errors.

        If everything is OK, print information about the build which is to happen.
        """
        if (
            self.website_plaintext_format != "md"
            and self.website_plaintext_format != "rst"
        ):
            raise ValueError(
                f"{self.website_plaintext_format} is not markdown (md) or restructured text (rst)."
            )

        print(f"Will build website into {self.build_dir} with;")
        print(f"\tSource branch: {self.source_branch}.")
        print(f"\tClean build  : {self.clean_build}")
        print(f"\tPlaintext fmt: {self.website_plaintext_format}")

        return

    def build(self) -> None:
        """
        Build the website using the set configurations.
        """
        print("BUILD STARTS")
        print("============")

        # Remove the pre-build directory if it persists from
        # a previous build for any reason
        safe_remove_dir(self.staging_dir)
        # Remove the build directory if requested
        if self.clean_build:
            safe_remove_dir(self.build_dir)

        # Copy the website templates and source to the staging directory as a starting point
        shutil.copytree(self.web_source_dir, self.staging_dir)

        # Create the _static folder in the staging directory if it was
        # gitignore-d in the source
        if not os.path.isdir(self.static_folder):
            os.mkdir(self.static_folder)

        # Populate the DataFrame with the information from the .stats.json
        # files on the source branch.
        self.parse_stats_files_to_df()

        # Fetch rendered HTML files from the source branch, if present
        # And write the hyperlink text to the necessary DataFrame column
        self.fetch_rendered_HTML()

        # Having fetched the HTML files, write the lookup table for the profiling outputs.
        self.write_profiling_lookup_table()

        # Produce plots of the selected statistics
        self.make_stats_plots()

        # Write the run statistics page of the website
        self.write_run_stats_page()

        # Build the website using sphinx.
        # Provide the staging directory as the source folder,
        # so that we render webpages with the lookup tables and plots
        # rather than the placeholder text.
        check_call(
            [
                "sphinx-build",
                "-b",
                "html",
                f"{str(self.staging_dir)}",
                f"{str(self.build_dir)}",
            ],
            cwd=GIT_ROOT,
        )

        # Remove the pre-build directory
        shutil.rmtree(self.staging_dir)

        print("==========")
        print("BUILD ENDS")
        return

    def fetch_rendered_HTML(self) -> None:
        """
        Fetch rendered profiling sessions from the source branch,
        saving the HTML files to the static directory in the staging area.

        This also populates the "Link" column of the DataFrame, so that
        each row now knows how to link to its profiling run output.
        """
        for index, row in self.df.iterrows():
            if row["html_output"] is None:
                self.df.loc[index, "HTML"] = None
                # There was no HTML file produced for this run,
                # so skip to the next
                continue

            # .stats.json files have absolute paths,
            # but only record the _relative_ path of their HTML files, if they exist.
            fetch_html_from = Path(row["stats_file"]).parent / Path(row["html_output"])

            # Move rendered HTML output to the static folder,
            # with the correct directory structure
            if self.flatten_profiling_html:
                html_file_name = self.profiling_html_dir / f"{fetch_html_from.name}"
            else:
                html_file_name = self.profiling_html_dir / fetch_html_from

            # Add the profiling output file to the static pages in the website
            file_contents(self.source_branch, fetch_html_from, html_file_name)

            # Populate this row in the DataFrame with the location of the
            # rendered HTML within the staging directory
            self.df.loc[index, "HTML"] = html_file_name

        # Create clickable markdown links in the Links column
        self.df["Link"] = self.df["HTML"].apply(
            write_page_link,
            relative_to=self.staging_dir,
            link_text="Output",
        )

        return

    def format_as_title(self, text: str) -> str:
        """
        Format the text string provided into a plaintext title,
        in the format corresponding to self.website_plaintext_format.
        """
        title_writer: Callable[[str], str]
        if self.website_plaintext_format == "rst":
            title_writer = lambda t: rst_title_format(t, "-")
        elif format == "md":
            title_writer = md_title_format
        return title_writer(text)

    def make_stats_plots(self) -> None:
        """
        Create and save plots of the statistics that are flagged as such.

        This produces a dictionary whose keys are the names of the plots, and whose values are
        the paths to the images of those plots.
        This dictionary populates the self.plot_dict attribute.
        """
        # Create the plot directory if it doesn't exist already
        if not os.path.exists(self.plot_folder):
            os.makedirs(self.plot_folder)

        # Initialise mapping of plots to titles as an empty dictionary
        self.plot_dict = dict()

        # For each statistic that produces a plot,
        # use matplotlib to produce the plot,
        # save the plot to the static staging directory,
        # and update our dictionary of plots so we know which statistic the plot corresponds to
        if not STATS.is_empty():
            for s in [stat for stat in STATS.statistics if stat.produces_plot]:
                # Check that there is numeric data to plot
                if self.df[s.dataframe_col_name].first_valid_index() is not None:
                    # Create and save plot
                    fig, ax = plt.subplots(figsize=self.size_of_plots)
                    self.df.plot(x="Start time", y=s.dataframe_col_name, ax=ax)
                    ax.set_xlabel("Run triggered on")
                    ax.set_ylabel(s.plot_y_label)
                    ax.set_title(s.plot_title)
                    fig.tight_layout()
                    fig.savefig(self.plot_folder / s.plot_svg_name, bbox_inches=None)

                    # Update dictionary that is tracking the plot just produced
                    self.plot_dict[s.plot_title] = self.plot_folder / s.plot_svg_name

        return

    def parse_stats_files_to_df(self) -> None:
        """
        Locate all statistics files on the source branch,
        and populate the DataFrame with their information.
        """
        # Locate stats files on the source branch
        stats_files = branch_contents(self.source_branch, f"*.{self.stats_file_ext}")

        # Initialise the DataFrame with the stats files
        self.df = pd.DataFrame({"stats_file": stats_files}, columns=DF_COLS)

        # Populate rows by reading stats files
        # Can probably do this with .apply() - revisit
        for index, row in self.df.iterrows():
            stats_file = row["stats_file"]
            self.df.loc[
                index, STATS.values("dataframe_col_name")
            ] = STATS.read_from_file(file=stats_file, branch=self.source_branch)

        # Set the commit field from the sha field
        self.df["Commit"] = self.df["sha"].apply(
            lambda sha: REPO.git.rev_parse("--short", sha)
        )

        return

    def write_profiling_lookup_table(self) -> str:
        """
        Create the source for the profiling results lookup table,
        by extracting the relevant columns from the DataFrame.
        """
        if self.website_plaintext_format == "rst":
            lookup_table = self.df[self.cols_for_lookup_table].to_markdown(
                index=False, tablefmt="grid"
            )
        else:
            lookup_table = self.df[self.cols_for_lookup_table].to_markdown(index=False)

        # Write the lookup page into the templated file.
        replace_in_file(
            self.profiling_table_file, PROFILING_TABLE_MATCH_STRING, lookup_table
        )

        return

    def write_run_stats_page(self) -> None:
        """
        Write the text for the webpage that will display statistics which are
        plotted across multiple profiling runs, then insert this into the webpage.
        """
        # Write the text for the statistics page into a string
        # Inserting titles and then the corresponding plots underneath
        stat_page_text = ""
        for plot_name, location in self.plot_dict.items():
            stat_page_text += self.format_as_title(plot_name)
            stat_page_text += write_image_link(
                location, self.staging_dir, plot_name, self.website_plaintext_format
            )
            stat_page_text += "\n"

        # Inject the text into the statistics plot webpage file
        replace_in_file(
            self.statistics_plots_file, RUN_PLOTS_MATCH_STRING, stat_page_text
        )

        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "source-branch",
        type=str,
        help="Git branch containing the statistics files (and rendered HTML) to be read.",
    )
    parser.add_argument(
        "-b",
        "--build-dir",
        type=Path,
        dest="build_dir",
        default=DEFAULT_BUILD_DIR,
        help=f"Directory to write HTML files into. Defaults to {DEFAULT_BUILD_DIR}",
    )
    parser.add_argument(
        "-f",
        "--flatten",
        dest="flatten_paths",
        action="store_true",
        help="Flatten the structure of the rendered profiling session (HTML) files when building.",
    )
    parser.add_argument(
        "-c",
        "--clean-build",
        dest="clean_build",
        action="store_true",
        help=f"Force-remove the build directory if it exists already. Will NOT execute on build directories outside the repository root, {GIT_ROOT}",
    )

    args = parser.parse_args()

    builder = WebsiteBuilder(
        # https://github.com/python/cpython/issues/59330#issuecomment-1533235029
        getattr(args, "source-branch"),
        Path(os.path.abspath(args.build_dir)),
        flatten_profiling_html=args.flatten_paths,
        clean_build=args.clean_build,
    )
    builder.build()
