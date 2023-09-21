Developer Documentation
=======================

.. _developers:

The purpose of this repository is to provide a storage space for profiling runs performed on the `Thanzi la Onse model <https://github.com/UCL/TLOmodel>`_, and a convenient way to page through the results that doesn't require developers to download the results for themselves.
The result is this repository, or specifically `the pages deployment <http://github-pages.ucl.ac.uk/TLOmodel-profiling>`_.

Profiling session outputs, ``.pyisession`` files, are pushed from the `model repository`_ when the profiling workflow has completed to the `source branch`_.
This triggers the `build-website <https://github.com/UCL/TLOmodel-profiling/blob/main/.github/workflows/build-website.yaml>`_ workflow which will run the `build script`_.
This script will parse the files on the `source branch`_, as well as update the developer docs with any changes, and deploy the new website over the old one.

On PRs, the profiling results HTML and developer docs HTML are required to build successfully before merging, however deployment only takes place when the ``build-website`` workflow is run on ``main``, or triggered as a direct result of new profiling results being pushed.

Build Steps
-----------

The website consists of two parts:

* The profiling results and statistics, which are created by the scripts in ``website_builder``, the results stored on the `source branch`_, and the content of the ``source`` folder.
* The developer documentation, which is created from the content of the ``source`` folder.

The website is built using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`_, which is invoked at the end of the ``website_builder/builder.py`` script (specifically within the ``Builder.build()`` method).
Before ``sphinx-build`` can be invoked, the profiling results on the `source branch`_ need to be parsed.
As such, the ``Builder`` first creates a *staging* directory, and copies the content of the ``source`` directory content into it as a starting point.

Files are then added to the staging directory as they are processed from the source branch; these additions consist primarily of profiling sessions that have been rendered as HTML, and plots for displaying runtime statistics.
The statistics files from the profiling runs are not copied across from the source branch - they are instead read into a ``DataFrame`` attribute of the ``Builder``.
This ``DataFrame`` allows us to produce the lookup table of profiling runs (which is inserted into the staged ``profiling.rst`` page), and the run statistics plots (inserted into the staged ``run-statistics.rst``).
Having done this pre-build step, ``sphinx`` will be invoked on the staged directory to build the HTML content of the website, creating the ``build`` directory with the HTML to be deployed.

An overview of the steps in the ``build_site.py`` script is provided below:

#. Copy the ``source`` directory into the staging directory.
#. Scan the source branch for all profiling output / statistics files. These typically carry the `.stats.json` extension.
#. Process additional statistics that were pushed across with the profiling outputs, and produce plots.
#. Fetch all rendered HTML pages from the source branch that contain profiling run information.
#. Write the lookup table to ``profiling.rst``.
#. Write the run statistics to ``run_statistics.rst``.
#. Invoke ``sphinx-build`` on the staging directory to create the website.

The ``Builder.df`` ``DataFrame`` keeps track of the summary stats and the correspondence between ``.stats.json`` files and HTML outputs.

Handling statistics via ``Statistic`` objects
---------------------------------------------

The statistics that we gather from the profiling runs can have multiple purposes.
Some are to be collected and plotted across multiple profiling runs; such as the CPU time or memory usage.
Others may hold information specific to a particular profiling run that provides information about how to
replicate the profiling results; like the commit SHA of the model that was profiled, workflow trigger
that set the profiling run off, and the time the run was triggered.

The statistics that are to be read from the profiling outputs are stored as ``Statistic`` objects (these can then be grouped into a ``StatisticsCollection``, which is a convenient wrapper class).
The ``statistics.py`` file then defines a static variable, ``STATS``, which corresponds to the statistics that the
profiling workflow on the main repository produce and which should be read-able from the output files.
If the profiling workflow is edited to produce different or additional statistics, or changes the format in which they
are saved, the corresponding entries in ``STATS`` should be updated / added accordingly.
They will then automatically be handled by the ``Builder``.

At a minimum, a ``Statistic`` must have a ``key_in_stats_file`` value specified.
This corresponds to the key which appears in the statistics files on the source branch, and will be used to extract the *value* of that statistic from the files.

If a ``plot_title`` is specified, the statistic is flagged as one to be plotted across multiple profiling runs.
In this case, the ``run_statistics.rst`` webpage will include a plot of the value of this statistic across each of the profiling runs.
``dataframe_col_name`` is the name of the column in the ``Builder`` ``DataFrame`` that will store the values of the statistic.
By default, it will take the same value as the ``key_in_stats_file``, but can be overwritten by providing an alternative string.
The ``dataframe_col_name`` is the header text used when writing the profiling lookup table.
As such, it is only necessary to provide this value if the statistic is intended to be displayed in the lookup table, and its ``key_in_stats_file`` needs to be made human-readable.

**Important:** If you intend to include a statistic in the lookup table, you will also need to make sure that its ``dataframe_col_name`` is passed to the list stored in ``Builder.cols_for_lookup_table``.

The remaining attributes of the ``Statistic`` class control subtler elements of the plot to be produced, the datatype that the statistic is expected to be, and a default value to assign if the statistic cannot be read.
There is also an optional ``converter`` attribute; that is a function which takes the value read from the ``key_in_stats_file``, operates on it, and produces the value to be saved as the statistic.
This is useful for quickly adding derived statistics to the ``Builder`` ``DataFrame``, without needing to manually operate on ``DataFrame`` columns.

Contents of the source branch
-----------------------------

Files on the source branch as assumed to have filenames in the following style:

.. code-block:: bash

   {trigger}_{run_number}_{commit_sha}.pyisession

* ``trigger``: The name of the ``github.event`` that triggered the profiling run.
* ``run_number``: The ``github.run_id`` of the workflow that ran.
* ``commit_sha``: The ``github.sha`` of the commit on which the profiling run was triggered.

In addition to the ``.pyisession`` files, additional statistics that cannot be saved by the profiler (like the size of the final simulation population) can also be present on the source branch.
The additional statistics are assumed to be in ``JSON`` files that carry the same filename as their profiling output counterpart, but with the ``.stats.json`` extension.
These files are processed by the build script when producing the additional statistics page.
Additional statistics are not required to be present; missing entries will be skipped or highlighted when rendering the corresponding page.

Glossary of Terms
-----------------

Build script
^^^^^^^^^^^^

The python script that creates the HTML files that are deployed to GitHub pages.

This is the ``website_builder/build_site.py`` script. 

Model repository
^^^^^^^^^^^^^^^^

The `Thanzi la Onse model <https://github.com/UCL/TLOmodel>`_ repository, containing the source code for the simulation itself.

Source branch
^^^^^^^^^^^^^

The branch of this repository that contains the ``.pyisession`` files, which themselves are the results of profiling sessions run on the `model repository`_.

Currently, the source branch is named `results <https://github.com/UCL/TLOmodel-profiling/tree/results>`_.