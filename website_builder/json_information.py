from datetime import datetime
import json
from pathlib import Path
from typing import Tuple

JSON_COLUMNS = [
    "Start Time",
    "duration (s)",
]
STATS_COLUMNS = []


def read_profiling_json(json_in: Path) -> Tuple[datetime, float]:
    """
    Read the provided json file, and return the JSON_COLUMNS data stored within in.
    The input json file should be a rendered output of a pyis session.

    Values are returned in the order that the JSON_COLUMNS variable gives their names.
    If values cannot be found, defaults are assigned (usually None to flag missing data).

    :param json_in: json file that is the rendered output of a .pyisession file.
    :returns: A tuple of values that correspond to the values in JSON_COLUMNS, extracted from the input file.
    """
    # Pre-emptively set outputs to None in case some keys cannot be found
    # We need a default for start_time as this will be the DataFrame index
    start_time = datetime.fromtimestamp(0.0)
    session_length_secs = None

    with open(json_in, "r") as json_file:
        pyis_session_data = json.load(json_file)

    # Grab information from the session file
    if "start_time" in pyis_session_data.keys():
        start_time = datetime.fromtimestamp(pyis_session_data["start_time"])
    if "duration" in pyis_session_data.keys():
        session_length_secs = pyis_session_data["duration"]

    return start_time, session_length_secs


def read_additional_stats(stats_file: Path) -> None:
    """
    Read the provided file, which is assumed to be a file containing additional statistics
    about a profiling run that cannot be conveyed by the pyis session file.
    Files recording additional statistics are assumed to be (able to be parsed as) json files.

    Values are returned in the order that the STATS_COLUMNS variable gives their names.
    If values cannot be found, defaults are assigned (usually None to flag missing data).

    :param json_in: A json-readable file containing statistics from a .pyisession.
    :returns: A tuple of values that correspond to the values in STATS_COLUMNS, extracted from the input file.
    """
    return
