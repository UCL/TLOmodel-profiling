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

    An instance of this class must have a ``key_in_stats_file`` corresponding to a key
    which appears in the statistics files produced by the profiling workflow.
    This key will be used to extract the value of that statistic from the files.

    If a ``plot_title`` is specified, the statistic is flagged to be plotted across multiple
    profiling runs. The corresponding webpage will include a plot of the value of this
    statistic across all available profiling runs.

    The ``dtype`` member can be used to ensure correct type casting occurs when reading statistics from files.
    Similarly, the ``converter`` attribute can be passed a function which acts on the value read from the statistics file, and saves the result as the value of the statistic. This can be used to avoid manual steps
    in the build process, such as converting timestamps (floats) to datetimes.

    ``dataframe_col_name`` is the name displayed in the lookup table for the statistic, and also the column name used internally by the :class:`builder.Builder` ``DataFrame``.

    A ``plot_y_label`` and ``plot_svg_name`` can be configured to change elements of the plot that is produced.

    The ``default_value`` will be used when the statistic cannot be read from a file.

    :param key_in_stats_file: Key in the statistics files produced by the profiling workflow that holds the value this statistic.
    :type key_in_stats_file: str
    :param plot_title: The title to display in the plot (showing change over time) of this statistic. If ``None`` (default), then no plot will be produced for this statistic.
    :type plot_title: str, optional
    :param dtype: The Python ``type`` that the statistic should be read as. Defaults to ``float``.
    :type dtype: type, optional
    :param dataframe_col_name: The column name in the :class:`builder.Builder` ``DataFrame`` and lookup table to use for this statistic. If ``None`` (default), use the ``key_in_stats_file`` value.
    :type dataframe_col_name: str, optional
    :param plot_y_label: The y-axis label to assign to the plot of this statistic across profiling runs. If ``None`` (default), use the ``plot_title``.
    :type plot_y_label: str, optional
    :param plot_svg_name: Name under which to save the plot svg that will be produced. If ``None`` (default), auto-generate a unique filename.
    :type plot_svg_name: str, optional
    :param default_value: Default value to assign to the statistic if it cannot be read or is missing from a statistics file. Defaults to ``None`` to flag missing data.
    :type default_value: Any, optional
    :param converter: A function to apply to the value read from the statistics file, with the result saved as the value of the statistic.
    :type converter: Callable[[Any] Any], optional
    """

    key_in_stats_file: str
    plot_title: str = None
    dtype: type = float
    dataframe_col_name: str = None
    plot_y_label: str = None
    plot_svg_name: str = None
    converter: Callable[[Any], Any] = None
    default_value: Any = None

    def __post_init__(self) -> None:
        """
        Post-instantiation checks:
        - If no DataFrame column provided, use the key from the stats file
        - If producing a plot, autofill y-axis label and filename if not provided
        """
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

        return

    @property
    def produces_plot(self) -> bool:
        """
        Whether this statistic should produce a plot of its value across profiling runs.
        """
        return self.plot_title is not None


class StatisticCollection:
    """
    A collection of Statistic objects.

    Defines convenient wrapper functions for extracting one particular attribute from
    each statistic in the collection, and for reading the values of all the statistics
    from a file using a single function.

    :param statistics: A list of statistics that should be collected - and plotted where requested.
    :type statistics: List[:class:`profiling_statistics.Statistic`]
    """

    statistics: List[Statistic]

    @property
    def is_empty(self) -> bool:
        """
        Return True if this instance contains no Statistics.
        """
        return len(self.statistics) == 0

    def __init__(self, *stats: Statistic) -> None:
        self.statistics = stats

    def values(self, attribute: str) -> List[Union[int, float, str]]:
        """
        For each Statistic in the collection, return the value stored under the attribute provided.

        :returns: ``[s.attribute for s in self.statistics]``
        """
        if attribute in Statistic.__annotations__.keys():
            return [getattr(s, attribute) for s in self.statistics]
        else:
            raise KeyError(f"Statistic has no attribute {attribute}")

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
        :returns: A list of values that correspond to the values of the statistics in this collection, extracted from the input file.
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


#: The STATIC collection of statistics that we are planning to extract
#: from the profiling runs.
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
    Statistic("disk_reads", dtype=int, dataframe_col_name="Disk reads"),
    Statistic("disk_writes", dtype=int, dataframe_col_name="Disk writes"),
    Statistic("disk_read_MB", dtype=float, dataframe_col_name="Disk read (MB)"),
    Statistic("disk_write_MB", dtype=float, dataframe_col_name="Disk write (MB)"),
    Statistic("disk_read_s", dtype=float, plot_title="Disk read time (s)"),
    Statistic("disk_write_s", dtype=float, plot_title="Disk write time (s)"),
)
