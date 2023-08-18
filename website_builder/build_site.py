import argparse
import os
from pathlib import Path
import shutil
from subprocess import check_call
from typing import Dict

import pandas as pd

from _paths import (
    DEFAULT_BUILD_DIR,
    GIT_ROOT,
    SRC_DIR,
)
from convert_pyis import convert_pyis
from filename_information import git_info_from_filename
from git_tree import branch_contents, file_contents
from json_information import read_additional_stats, read_profiling_json
from json_information import JSON_COLUMNS, STATS_COLUMNS
from stat_plots import make_stats_plots, write_string_for_run_plots
from utils import (
    clean_build_directory,
    create_dump_folder,
    replace_in_file,
    write_page_link,
)

TABLE_EXTRA_COLUMNS = [
    "HTML",
    "Link",
    "Commit",
    "Triggered by",
]
DF_COLS = set(TABLE_EXTRA_COLUMNS) | set(JSON_COLUMNS) | set(STATS_COLUMNS)
PROFILING_TABLE_MATCH_STRING = "<<<MATCH_PATTERN_FOR_MARKDOWN_TABLE_INSERT>>>"
RUN_PLOTS_MATCH_STRING = "<<<MATCH_PATTERN_FOR_RUN_STATS_PLOTS>>>"
DESCRIPTION = (
    "Build the website deployment for the profiling results, "
    "placing the resulting files in the build directory."
)


class WebsiteBuilder:
    """
    Handles the construction of the gh-pages website, as per the process detailed
    in http://github-pages.ucl.ac.uk/TLOmodel-profiling/repo-overview.html.
    """

    # The "site DataFrame" where each row is a pyis session, and the corresponding information
    df: pd.DataFrame
    # Plots that are made from the run statistics, (key, value) = (name, plot file location).
    plots: Dict[str, Path]

    # Repository branch on which source .pyisession files are located.
    source_branch: str
    # Directory to write website files to.
    build_dir: Path

    @property
    def pre_build_dir(self) -> Path:
        """
        The intermediate folder that sphinx-build will use as it's source for building the website.
        This folder will contain static files that have to be generated from the results stored on the corresponding branch; such as:
        * The static HTML files rendered from pyinstrumment sessions,
        * The rst files with the lookup tables inserted,
        * The run-statistics plots.
        """
        return Path(str(self.build_dir) + "-pre-build")

    # Dump folder for temporary files
    dump_folder: Path

    @property
    def _static_folder(self) -> Path:
        """
        The folder containing static html files that are to be linked to.
        """
        return self.pre_build_dir / "_static"

    @property
    def profiling_lookup_src(self) -> Path:
        """
        The file containing the
        <<<MATCH_PATTERN_FOR_MARKDOWN_TABLE_INSERT>>>,

        which is where the profiling results lookup table will be inserted.
        """
        return self.pre_build_dir / "profiling.rst"

    @property
    def run_stats_src(self) -> Path:
        """
        The file containing the
        <<<MATCH_PATTERN_FOR_RUN_STATS_PLOTS>>>,

        which is where the run statistics plots will be inserted.
        """
        return self.pre_build_dir / "run-statistics.rst"

    @property
    def run_stats_plots(self) -> Path:
        """
        The folder within the build directory that will contain any plots that are generated from the statistics collected across the profiling runs.
        """
        return self._static_folder / "plots"

    @property
    def pyis_html_folder(self) -> Path:
        """
        The folder within the build directory that will contain any HTML files generated from pyisession files.
        """
        return self._static_folder / "pyis_html"

    # If True, the static_html_folder (containing the HTML renderings of the pyis sessions),
    # will be flat rather than preserving the structure on the source branch.
    flatten_paths: bool

    def __init__(
        self,
        source_branch: str,
        clean_build: bool = False,
        build_dir: Path = DEFAULT_BUILD_DIR,
        flatten_paths: bool = True,
    ) -> None:
        """
        Initialise the builder by providing the branch the pyis files are stored,
        and build parameters.

        :param source_branch: Branch of the git repo on which pyis files are stored.
        :param clean_build: Purge build directory of its contents before beginning.
        :param build_dir: The directory to write the website files to.
        :param flatten_paths: If True, the directory structure of the source branch will be ignored, and the build directory will be flat.
        """
        self.source_branch = source_branch
        print(f"Preparing website build using source branch: {self.source_branch}")

        # Initialise DataFrame by pulling pyis files from source branch
        pyis_files = branch_contents(source_branch, "*.pyisession")
        if len(pyis_files) < 1:
            raise RuntimeError(
                f"Source branch {self.source_branch} contains no pyisession files to read."
            )
        else:
            print(f"Found {len(pyis_files)} pyis files on source branch.")

        self.df = pd.DataFrame({"pyis": pyis_files})
        # Add extra columns to the DataFrame, to be populated later
        for col in DF_COLS:
            self.df[col] = None

        self.build_dir = build_dir
        if clean_build:
            clean_build_directory(self.pre_build_dir)
            clean_build_directory(self.build_dir)
        # Copy the source to the build directory as a starting point
        shutil.copytree(SRC_DIR, self.pre_build_dir)
        # Create the _static folder in the build directory if it was .gitignore-d in source
        if not os.path.isdir(self._static_folder):
            os.mkdir(self._static_folder)

        self.flatten_paths = flatten_paths
        # Create the dump folder (and build directory if needed)
        self.dump_folder = create_dump_folder(self.pre_build_dir)

        # Populate information that can be inferred by examining the filenames
        self._infer_filename_information()
        return

    def _infer_filename_information(self) -> None:
        """
        Infer information about the profiling runs by examining the filenames the
        pyis sessions are saved under.

        Filenames are assumed to obey the convention described in filename_information.py.
        """
        # Determine workflow trigger, SHA, and commit hashes
        self.df[["Triggered by", "SHA", "Commit"]] = (
            self.df["pyis"].apply(git_info_from_filename).apply(pd.Series)
        )
        return

    def write_pyis_to_html(self):
        """
        Render the HTML output of all pyis files on the source branch,
        writing the outputs to the build directory.

        Updates the site DataFrame to keep track of which HTML file corresponds
        to which pyis file.
        """

        # Render each file to HTML, and save to the output directory
        for index in self.df.index:
            pyis_file = Path(self.df["pyis"][index])
            dump_file = self.dump_folder / pyis_file
            # Fetch the relevant pyis file from the source branch
            file_contents(self.source_branch, pyis_file, dump_file)

            # Create HTML file name
            if self.flatten_paths:
                html_file_name = (
                    self.pyis_html_folder / f"{pyis_file.stem}_{index}.html"
                )
            else:
                html_file_name = (
                    self.pyis_html_folder
                    / f"{pyis_file.parent}"
                    / f"{pyis_file.stem}_{index}.html"
                )

            # Render HTML from the pulled pyis session
            convert_pyis(dump_file, html_file_name, "html")

            # Populate the df entry with the HTML output corresponding to this pyis session
            self.df["HTML"][index] = html_file_name

        # Create clickable markdown links in the Links column
        self.df["Link"] = self.df["HTML"].apply(
            write_page_link,
            relative_to=self.pre_build_dir,
            link_text="Profiling results",
        )
        return

    def write_profiling_lookup_table(self) -> str:
        """
        Create the markdown source for the profiling results lookup table,
        by extracting the relevant columns from the DataFrame.
        """
        COLS_FOR_LOOKUP_TABLE = [
            "Start Time",
            "Link",
            "Commit",
            "Triggered by",
        ]
        rst_table = self.df[COLS_FOR_LOOKUP_TABLE].to_markdown(tablefmt="grid")

        # Write the lookup page
        replace_in_file(
            self.profiling_lookup_src, PROFILING_TABLE_MATCH_STRING, rst_table
        )
        return

    def collect_run_stats(self, stats_file_extension: str = "stats.json"):
        """
        Read any saved stats (if they exist) for each pyis session and populate
        the columns of the DataFrame with this information.
        """
        for index in self.df.index:
            # Fetch pyis file if it doesn't already exist
            pyis_file = Path(self.df["pyis"][index])
            dump_file = self.dump_folder / pyis_file
            if not os.path.exists(dump_file):
                file_contents(self.source_branch, pyis_file, dump_file)

            # Convert to json and read information into DataFrame
            json_file = self.dump_folder / f"{pyis_file.stem}_{index}.json"
            convert_pyis(dump_file, json_file, "json", verbose=False)
            self.df.loc[index, JSON_COLUMNS] = read_profiling_json(json_file)

            # Fetch additional stats file, if it exists and there are additional stats to record
            if STATS_COLUMNS:
                stats_file = (
                    pyis_file.parent / f"{pyis_file.stem}.{stats_file_extension}"
                )
                dump_stats_file = self.dump_folder / stats_file
                try:
                    file_contents(
                        self.source_branch,
                        stats_file,
                        dump_file,
                    )
                except FileNotFoundError as e:
                    # File does not exist on the source branch, cannot write stats for this entry
                    print(
                        f"Skipping {pyis_file}: expected stats file ({stats_file}) not found"
                    )
                    continue
                # Record additional stats as recorded in the stats file
                self.df.loc[index, STATS_COLUMNS] = read_additional_stats(
                    dump_stats_file
                )

        # All additional stats have been pulled and added to the DataFrame
        # Sort the DataFrame by start_time
        self.df.sort_values("Start Time", ascending=True, inplace=True)

    def write_run_stats_page(self) -> None:
        """ """
        self.plots = make_stats_plots(self.df, self.run_stats_plots)

        # Write markdown to include plots in site
        plot_markdown = write_string_for_run_plots(self.plots, self.pre_build_dir)

        # Write the file
        replace_in_file(self.run_stats_src, RUN_PLOTS_MATCH_STRING, plot_markdown)
        return

    def build(self) -> None:
        """
        Build the website source files and populate the site DataFrame.
        """
        print(f"Building website in directory {self.pre_build_dir}")
        # Infer additional run stats from the pyis files, and
        # supporting stats.json files, if present
        self.collect_run_stats()

        # Build the HTML files for the profiling outputs
        self.write_pyis_to_html()

        # Build the lookup page for navigating profiling run outputs
        self.write_profiling_lookup_table()

        # Build the run statistics page
        self.write_run_stats_page()

        # Cleanup the dump folder
        shutil.rmtree(self.dump_folder)

        # Build the website using sphinx
        check_call(
            [
                "sphinx-build",
                "-b",
                "html",
                f"{str(self.pre_build_dir)}",
                f"{str(self.build_dir)}",
            ],
            cwd=GIT_ROOT,
        )
        # Remove the pre-build directory
        shutil.rmtree(self.pre_build_dir)
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "source_branch",
        type=str,
        help="Branch to pull pyis session files from.",
    )
    parser.add_argument(
        "build_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help=f"Directory to write HTML files into. Defaults to {DEFAULT_BUILD_DIR}",
    )
    parser.add_argument(
        "-f",
        "--flatten",
        dest="flatten_paths",
        action="store_true",
        help="Flatten the HTML output in the build directory.",
    )
    parser.add_argument(
        "-c",
        "--clean-build",
        dest="clean_build",
        action="store_true",
        help=f"Force-remove the build directory if it exists already. Will NOT execute on build directories outside the repository root, {GIT_ROOT}",
    )

    args = parser.parse_args()
    args.build_dir = Path(os.path.abspath(args.build_dir))

    builder = WebsiteBuilder(**vars(args))
    builder.build()
