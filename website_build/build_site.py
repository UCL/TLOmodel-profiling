import argparse
import os
from pathlib import Path
import shutil
from typing import Dict

import pandas as pd

from _paths import (
    DEFAULT_BUILD_DIR,
    GIT_ROOT,
    INDEX_PAGE,
    PROFILING_LOOKUP_TEMPLATE,
    RUN_STATS_LOOKUP_TEMPLATE,
)
from convert_pyis import pyis_to_html, pyis_to_json
from filename_information import git_event, git_SHA
from git_tree import branch_contents, file_contents
from json_information import read_additional_stats, read_profiling_json
from json_information import JSON_COLUMNS, STATS_COLUMNS
from stat_plots import make_stats_plots, markdown_for_run_plots
from utils import clean_build_directory, create_dump_folder, write_md_link

TABLE_EXTRA_COLUMNS = [
    "HTML",
    "Link",
    "Commit",
    "Triggered by",
]
DF_COLS = set(TABLE_EXTRA_COLUMNS) | set(JSON_COLUMNS) | set(STATS_COLUMNS)
MARKDOWN_REPLACEMENT_STRING = "<<<MATCH_PATTERN_FOR_MARKDOWN_TABLE_INSERT>>>"
RUN_PLOTS_REPLACEMENT_STRING = "<<<MATCH_PATTERN_FOR_RUN_STATS_PLOTS>>>"
DESCRIPTION = (
    "Build the website deployment for the profiling results, "
    "placing the resulting files in the build directory."
)


class WebsiteBuilder:
    """
    Handles the construction of the gh-pages website,
    by building the source files from the .pyisession files that the source branch contains.
    """

    # If True, the contents of the build directory will be removed before building again.
    # Only works if the build directory lies within (a subdirectory of) the repository root.
    clean_build: bool

    # The "site DataFrame" where each row is a pyis session, and the corresponding information
    df: pd.DataFrame
    # Plots that are made from the run statistics, (key, value) = (name, plot file location).
    plots: Dict[str, Path]

    # Repository branch on which source .pyisession files are located.
    source_branch: str
    # Directory to write website files to.
    build_dir: Path
    # Dump folder for temporary files
    dump_folder: Path

    # If True, the pyis_html subfolder, containing the HTML renderings of the pyis sessions,
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
            print(f"Found {len(pyis_files)} on source branch.")

        self.df = pd.DataFrame({"pyis": pyis_files})
        # Add extra columns to the DataFrame, to be populated later
        for col in DF_COLS:
            self.df[col] = None

        self.build_dir = build_dir
        self.clean_build = clean_build
        if self.clean_build:
            clean_build_directory(self.build_dir)
        self.flatten_paths = flatten_paths

        # Create the dump folder (and build directory if needed)
        self.dump_folder = create_dump_folder(self.build_dir)

        # Populate information that can be inferred by examining the filenames
        self._infer_filename_information()
        return

    def _infer_filename_information(self) -> None:
        """
        Infer information about the profiling runs by examining the filenames the
        pyis sessions are saved under.

        Filenames are assumed to obey the convention described in filename_information.py.
        """
        # Determine SHA and commit hashes
        self.df[["SHA", "Commit"]] = self.df["pyis"].apply(git_SHA).apply(pd.Series)

        # Workflow event trigger
        self.df["Triggered by"] = self.df["pyis"].apply(git_event)

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
                    self.build_dir / "pyis_html" / f"{pyis_file.stem}_{index}.html"
                )
            else:
                html_file_name = (
                    self.build_dir
                    / "pyis_html"
                    / f"{pyis_file.parent}"
                    / f"{pyis_file.stem}_{index}.html"
                )

            # Render HTML from the pulled pyis session
            pyis_to_html(dump_file, html_file_name)

            # Populate the df entry with the HTML output corresponding to this pyis session
            self.df["HTML"][index] = html_file_name

        # Create clickable markdown links in the Links column
        self.df["Link"] = self.df["HTML"].apply(
            write_md_link, relative_to=self.build_dir, link_text="Profiling results"
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
        markdown_table = self.df[COLS_FOR_LOOKUP_TABLE].to_markdown()

        # Write the lookup page
        lookup_table_page = self.build_dir / "profiling_index.md"
        with open(PROFILING_LOOKUP_TEMPLATE, "r") as f:
            lookup_page_contents = f.read()
        template_contents = lookup_page_contents.split(MARKDOWN_REPLACEMENT_STRING)
        # Write processed lookup page to the build directory
        with open(lookup_table_page, "w") as f:
            f.write(template_contents[0])
        with open(lookup_table_page, "a") as f:
            f.write(markdown_table)
        with open(lookup_table_page, "a") as f:
            f.write(template_contents[1])
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
            pyis_to_json(dump_file, json_file)
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
        self.plots = make_stats_plots(self.df, self.build_dir / "plots")

        # Write markdown to include plots in site
        plot_markdown = markdown_for_run_plots(self.plots, self.build_dir)

        # Write the file
        run_stats_index = self.build_dir / "run_statistics.md"
        with open(RUN_STATS_LOOKUP_TEMPLATE, "r") as f:
            lookup_page_contents = f.read()
        template_contents = lookup_page_contents.split(RUN_PLOTS_REPLACEMENT_STRING)
        # Write processed lookup page to the build directory
        with open(run_stats_index, "w") as f:
            f.write(template_contents[0])
        with open(run_stats_index, "a") as f:
            f.write(plot_markdown)
        with open(run_stats_index, "a") as f:
            f.write(template_contents[1])

    def build(self) -> None:
        """
        Build the website source files and populate the site DataFrame.
        """
        print(f"Building website in directory {self.build_dir}")
        # Infer additional run stats from the pyis files, and
        # supporting stats.json files, if present
        self.collect_run_stats()

        # Build the HTML files for the profiling outputs
        self.write_pyis_to_html()

        # Build the lookup page for navigating profiling run outputs
        self.write_profiling_lookup_table()

        # Build the run statistics page
        self.write_run_stats_page()

        # Move index page source file into the build directory
        shutil.copy(INDEX_PAGE, self.build_dir / "index.md")

        # Cleanup the dump folder
        shutil.rmtree(self.dump_folder)
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
