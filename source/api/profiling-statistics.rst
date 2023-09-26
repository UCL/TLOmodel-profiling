Handling Statistics
===================

The statistics that we gather from the profiling runs can have multiple purposes.
Some are to be collected and plotted across multiple profiling runs; such as the CPU time or memory usage.
Others may hold information specific to a particular profiling run that provides information about how to
replicate the profiling results; like the commit SHA of the model that was profiled, workflow trigger
that set the profiling run off, and the time the run was triggered.

The statistics that are to be read from the profiling outputs are stored as :class:`profiling_statistics.Statistic` objects (these can then be grouped into a :class:`profiling_statistics.StatisticsCollection`, which is a convenient wrapper class).
The ``profiling_statistics.py`` file then defines a static variable, :class:`profiling_statistics.STATS`, which corresponds to the statistics that the profiling workflow on the main repository produce and which should be read-able from the output files.
If the profiling workflow is edited to produce different or additional statistics, or changes the format in which they
are saved, the corresponding entries in :class:`profiling_statistics.STATS` should be updated / added accordingly.
They will then automatically be handled by the :class:`builder.Builder`.

The ``Statistic`` class
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: profiling_statistics.Statistic
    :members:

Examples
--------

Define a statistic whose key in the statistics files is "*trigger*", should be saved as a string, and displayed in the lookup table under the heading "*Triggered by*".

.. code-block:: python

    Statistic("trigger", dtype=str, dataframe_col_name="Triggered by"),

Define a statistic containing a duration of time.
The value as read from the "duration" field in the statistics file actually contains the time duration in seconds, and we want it in minutes.
As such, pass a ``lambda`` function to the converter field so that Python knows to run this conversion when reading this statistic from the files.

.. code-block:: python

    convert = lambda t_secs: t_secs / 60.
    Statistic("duration", dtype=float, dataframe_col_name="Session duration (min)", converter = convert),

Collections of ``Statistic`` s
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`profiling_statistics.StatisticCollection` class provides a convenient wrapper for looping through the statistics that we gather from the profiling runs.

.. autoclass:: profiling_statistics.StatisticCollection
   :members:

Example: The ``STATS`` constant
-------------------------------

The :class:`profiling_statistics.STATS` constant initialises a :class:`profiling_statistics.StatisticCollection` instance which defines all of the variables we expect to receive in the profiling-workflow-produced-statistics files.
The :class:`builder.Builder` references this constant when constructing the profiling results website; so if future updates add another statistic to the profiling outputs, an additional :class:`profiling_statistics.Statistic` can be added to the :class:`profiling_statistics.STATS` constant, and it will be automatically included in the next build of the website.
