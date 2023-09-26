Building the website
====================

The :class:`builder.Builder` class is the object that is responsible for assembling the profiling website, as well as the developer documentation.
The choice to use a class over a script or function was due to a combination of minimising parameter passing balanced against the ability to break the process of building the website into manageable, human-readable chunks.

The website build can be triggered by passing the ``website_builder/builder.py`` script to Python on the command line.
You may pass the ``--help`` option for additional options, which are just convenience wrappers for :class:`builder.Builder` class functionality. 

.. code-block:: bash

    python website_builder/builder.py

It is also worth mentioning a few constants that are defined in this module.

- ``PROFILING_TABLE_MATCH_STRING``: This string appears in `profiling.rst`, and is replaced with the contents of the lookup table that is inserted into that page.
- ``RUN_PLOTS_MATCH_STRING``: This string appears in `run-statistics.rst`, and is replaced with the various plots that are produced for the :class:`profiling_statistics.Statistic` instances that require plotting.
- ``DF_EXTRA_COLUMNS``: These are additional columns that need to be computed from the statistics read in, or from examination of the source branch tree structure.

The ``Builder``
---------------

The heavy-lifting of the website construction is done by :class:`builder.Builder`.
Build options are set on initialisation (although there is nothing stopping you from editing attribute values of a class instance at runtime), and the construction can be invoked with the :class:`builder.Builder.build` method.

.. autoclass:: builder.Builder
    :members: