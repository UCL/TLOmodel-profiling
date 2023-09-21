from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, List, Union

from git_tree import file_contents
from utils import timestamp_to_time


@dataclass
class Statistic:
    """
    A general class for tracking information about a statistic captured by the profiling run.

    The statistics that we gather from the profiling runs can have multiple purposes.
    Some are to be collected and plotted across multiple profiling runs; such as the CPU time or memory usage.
    Others may hold information specific to a particular profiling run that provides information about how to
    replicate the profiling results; like the commit SHA of the TLOmodel that was profiled, workflow trigger
    that set the profiling run off, and the time the run was triggered.

    At a minimum, an instance of this class must have a key_in_stats_file value which corresponds to a key
    which appears in the statistics files produced by the profiling workflow.
    This key will be used to extract the _value_ of that statistic from the files.

    If a plot_title is specified, the statistic is flagged as one to be plotted across multiple
    profiling runs. In this case, the run statistics webpage will include a plot of the value of this
    statistic over time.

    The dtype argument can be used to ensure correct type casting occurs when reading statistics from files.
    On a related note, the converter attribute can be passed a function which acts on the value read from the
    key_in_stats_file and saves the result as the value of the statistic. This can be used to avoid manual steps
    in the build process, such as converting timestamps (floats) to datetimes.

    dataframe_col_name is the name of the column in the website DataFrame that will store the values
    of the statistic. By default, it will take the same value as the key_in_stats_file. Overwriting it will
    change how the column header is written in the profiling lookup table (if the column is included at all).

    The plot_y_label and plot_svg_name can be configured to change the y-label axis which appears in the plot
    and the name under which it is saved (if a plot is produced).

    The default_value will be used when the statistic cannot be read from a file. This is best set to None,
    since the DataFrame will then correctly identify it as missing data, however it can also be used to handle
    cases where data is omitted from the statistics files in the event it takes the default value.
    """

    # The key in the stats file under which this can be found
    key_in_stats_file: str
    # The title to assign to the plot of this statistic across profiling runs
    # If this is NoneType, this statistic does not produce a plot
    plot_title: str = None
    # Type of variable the statistic should be read into
    dtype: type = float
    # The column name in the website builder DataFrame where this statistic is stored
    dataframe_col_name: str = None
    # The y-axis label to assign to the plot of this statistic across profiling runs
    plot_y_label: str = None
    # Name under which to save the plot svg that will be produced
    plot_svg_name: str = None

    # Function to apply to any value read in from the stats file,
    # to convert the data input to the desired format
    converter: Callable[[Any], Any] = None
    # Default value to apply to the statistic if it cannot be read from
    # a file.
    default_value: Any = None

    def __post_init__(self) -> None:
        # If no DataFrame column name was provided,
        # use the key from the file it was read from as a proxy
        if self.dataframe_col_name is None:
            self.dataframe_col_name = self.key_in_stats_file
        # If we are producing a plot, ensure that plot information
        # is populated, and assign defaults if not.
        if self.plot_title is not None:
            if self.plot_y_label is None:
                self.plot_y_label = self.plot_title
            if self.plot_svg_name is None:
                self.plot_svg_name = "".join(
                    filter(str.isalnum, self.plot_title.lower().replace(" ", "_"))
                )
            if len(self.plot_svg_name) < 4 or self.plot_svg_name[-4:] != ".svg":
                self.plot_svg_name += ".svg"

    @property
    def produces_plot(self) -> bool:
        return self.plot_title is not None


class StatisticCollection:
    """
    A collection of Statistic objects.

    Defines convenient wrapper functions for extracting one particular attribute from
    each statistic in the collection, and for reading the values of all the statistics
    from a file using a single function.
    """

    # A list of statistics that should be collected and plotted, where possible
    statistics: List[Statistic]

    @property
    def is_empty(self) -> bool:
        """
        Return True if this instance contains no Statistics.
        """
        return len(self.statistics) == 0

    def __init__(self, *stats: Statistic) -> None:
        self.statistics = stats

    def values(self, key: str) -> List[Union[int, float, str]]:
        """
        Fetch the values stored under the key provided,
        of each of the Statistics in this collection.
        """
        if key in Statistic.__annotations__.keys():
            return [getattr(s, key) for s in self.statistics]
        else:
            raise KeyError(f"Statistic has no attribute {key}")

    def read_from_file(
        self, file: Path = None, branch: str = None, string: str = None
    ) -> List[Union[int, float, str]]:
        """
        Parse the statistics in this collection from the values provided in the file, or
        a string with the parsed contents.
        File (or string representing parsed file) should be parse-able as a json.

        Values are returned in the order that the .values() method returns their names.
        If values cannot be found, defaults are assigned (usually None to flag missing data).

        :param file: A json-readable file containing values of the statistics in this collection.
        :param branch: If provided, read the file from an alternative branch to the one that is currently checked-out.
        :param string: A string representing a parsed json file, which is of the format described previously.
        :returns: A list of values that correspond to the values of the statistics in this collection,
        extracted from the input file.
        """
        if (file is not None) and (string is not None):
            raise RuntimeError(
                f"Exactly one of file ({file}) and string ({string}) should be provided."
            )
        elif file is not None:
            if branch is not None:
                # Reading from file on another branch
                string = file_contents(branch, file)
                loaded_stats = json.loads(string)
            else:
                # Straight-up read
                with open(file, "r") as f:
                    loaded_stats = json.load(f)
        else:
            # Parse from string
            loaded_stats = json.loads(string)

        values = []
        # Iterate through the statistics, reading each from the file
        for s in self.statistics:
            if s.key_in_stats_file in loaded_stats.keys():
                # Load value from file
                value = loaded_stats[s.key_in_stats_file]
                # Apply converter function if necessary
                if s.converter is not None:
                    value = s.converter(value)
            else:
                # Assign default value,
                # statistic could not be found in file
                value = s.default_value
            values.append(value)
        # Return the list of values
        return values


# The STATIC collection of statistics that we are planning to extract
# from the profiling runs.
STATS = StatisticCollection(
    Statistic("sha", dtype=str),
    Statistic("trigger", dtype=str, dataframe_col_name="Triggered by"),
    Statistic("html_output", dtype=str),
    Statistic(
        "start_time",
        dtype=str,
        converter=timestamp_to_time,
        dataframe_col_name="Start time",
    ),
    Statistic("duration", dtype=float, dataframe_col_name="Session duration (s)"),
    Statistic(
        "cpu_time", plot_title="CPU Time", dtype=float, dataframe_col_name="CPU time"
    ),
    Statistic("pop_df_rows", plot_title="# rows in population dataframe", dtype=int),
    Statistic("pop_df_cols", plot_title="# cols in population dataframe", dtype=int),
    Statistic(
        "pop_df_mem_mb",
        plot_title="Memory used by population dataframe",
        dtype=float,
        plot_y_label="Dataframe size (MB)",
    ),
    Statistic(
        "pop_df_times_extended",
        plot_title="# times population dataframe was extended",
        dtype=int,
        plot_y_label="Number of extensions",
    ),
    Statistic("disk_reads", dtype=int),
    Statistic("disk_writes", dtype=int),
    Statistic("disk_read_MB", dtype=float),
    Statistic("disk_write_MB", dtype=float),
    Statistic("disk_read_s", dtype=float),
    Statistic("disk_write_s", dtype=float),
)
