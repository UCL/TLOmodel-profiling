from dataclasses import dataclass
import json
from pathlib import Path
from typing import List, Tuple, Union

# STATS_COLUMNS.values() are the column names under which we
# want to identify the statistics, and the names we will use in
# plot titles.
# STATS_COLUMNS.keys() are the corresponding keys in the file
# containing the statistics that the values should be read from
# STATS_COLUMNS = {
#     "pop_df_rows": "Pop. dataframe rows",
#     "pop_df_cols": "Pop. dataframe cols",
#     "pop_df_mem_mb": "Pop. dataframe memory usage (MBs)",
#     "pop_df_times_extended": "Number of times pop. dataframe was extended",
# }


@dataclass
class Statistic:
    """
    Class for tracking information about a statistic captured by the profiling run,
    but which is obtained from the supplementary statistics file rather than the
    pyisession file.
    """

    # The key in the stats file under which this can be found
    key_in_stats_file: str
    # The title to assign to the plot of this statistic across profiling runs
    plot_title: str
    # Type of variable the statistic should be read into
    dtype: type = float
    # The column name in the website builder dataframe where this statistic is stored
    dataframe_col_name: str = None
    # The y-axis label to assign to the plot of this statistic across profiling runs
    plot_y_label: str = None
    # Name under which to save the plot svg that will be produced
    plot_svg_name: str = None

    def __post_init__(self) -> None:
        if self.dataframe_col_name is None:
            self.dataframe_col_name = self.key_in_stats_file
        if self.plot_y_label is None:
            self.plot_y_label = self.plot_title
        if self.plot_svg_name is None:
            self.plot_svg_name = "".join(
                filter(str.isalnum, self.plot_title.lower().replace(" ", "_"))
            )
        if len(self.plot_svg_name) < 4 or self.plot_svg_name[-4:] != ".svg":
            self.plot_svg_name += ".svg"


class StatisticCollection:
    """
    The collection of statistics that we wish to read from the additional
    statistics files that are produced alongside the profiling runs.
    """

    # A list of statistics that should be collected and plotted, where possible
    statistics: List[Statistic]

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

    def is_empty(self) -> bool:
        return len(self.statistics) == 0


# The STATIC collection of statistics that we are planning to extract
# from the profiling runs.
STATS = StatisticCollection(
    Statistic("pop_df_rows", "# rows in population dataframe", int),
    Statistic("pop_df_cols", "# cols in population dataframe", int),
    Statistic(
        "pop_df_mem_mb",
        "Memory used by population dataframe",
        float,
        plot_y_label="Dataframe size (MB)",
    ),
    Statistic(
        "pop_df_times_extended",
        "# times population dataframe was extended",
        int,
        plot_y_label="Number of extensions",
    ),
)


def read_additional_stats(stats_file: Path) -> Tuple[int, int, float, int]:
    """
    Read the provided file, which is assumed to be a file containing additional statistics
    about a profiling run that cannot be conveyed by the pyis session file.
    Files recording additional statistics are assumed to be (able to be parsed as) json files.

    Values are returned in the order that the STATS_COLUMNS variable gives their names.
    If values cannot be found, defaults are assigned (usually None to flag missing data).

    :param json_in: A json-readable file containing statistics from a .pyisession.
    :returns: A tuple of values that correspond to the values in STATS_COLUMNS, extracted from the input file.
    """
    with open(stats_file, "r") as f:
        stats = json.load(f)

    return (stats[key] for key in STATS.values("key_in_stats_file"))
