.. TLO Model: Profiling documentation master file, created by
   sphinx-quickstart on Thu Aug 17 13:46:22 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TLO Model: Profiling, Developer Documentation!
=========================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   reference

Overview
========

The purpose of this repository is to provide a storage space for profiling runs performed on the `Thanzi la Onse model <https://github.com/UCL/TLOmodel>`_, and a convenient way to page through the results that doesn't require developers to download the results for themselves.
The result is this repository, or specifically `the pages deployment <http://github-pages.ucl.ac.uk/TLOmodel-profiling>`_.

Profiling session outputs, ``.pyisession`` files, are pushed from the `model repository`_ when the profiling workflow has completed to the `source branch`_.
This triggers the `build-website <https://github.com/UCL/TLOmodel-profiling/blob/main/.github/workflows/build-website.yaml>`_ workflow which will run the `build script`_.
This script will parse the files on the source branch, as well as update the developer docs with any changes, and deploy the new website over the old one.

On PRs, the profiling results HTML and developer docs HTML are required to build successfully before merging, however deployment only takes place when the ``build-website`` workflow is run on ``main``, or triggered as a direct result of new profiling results being pushed.

Build Steps
-----------

The build steps can be summarised as follows.

* Use `doxygen <https://www.doxygen.nl/>`_ to build the developer docs; documenting the functions, classes, and scripts that perform the heavy lifting.
* Run the build script to process the profiling results.
   #. Scan the source branch for all ``pyisession`` files
   #. Render all profiling output files to HTML
   #. Process additional statistics that were pushed across with the profiling outputs, and produce plots.
   #. Write the lookup table, profiling_index.md
   #. Write the run statistics, run_statistics.md
   #. Include the index page in the build directory
* Combine the ``doxygen`` build and profiling results, and deploy to GitHub pages.

The build script makes use of a ``pandas`` DataFrame to keep track of the summary stats and the correspondence between ``.pyisession`` files and HTML outputs, for example.

Contents of the source branch
-----------------------------

Files on the source branch as assumed to have filenames in the following style:

.. code-block:: bash

   {trigger}_{run_number}_{commit_sha}.pyisession

* ``trigger``: The name of the ``github.event`` that triggered the profiling run.
* ``run_number``: The ``github.run_id`` of the workflow that ran.
* ``commit_sha``: The ``github.sha`` of the commit on which the profiling run was triggered.

In addition to the ``pyisession`` files, additional statistics that cannot be saved by the profiler (like the size of the final simulation population) can also be present on the source branch.
The additional statistics are assumed to be in ``JSON`` files that carry the same filename as their profiling output counterpart, but with the ``.stats.json`` extension.
These files are processed by the build script when producing the additional statistics page.
Additional statistics are not required to be present, as missing entries will be skipped or highlighted when rendering the corresponding page.

Glossary of Terms
-----------------

Build script
^^^^^^^^^^^^

The python script that creates the HTML files that are deployed to GitHub pages.

This is the ``website_build/build_site.py`` script. 

Model repository
^^^^^^^^^^^^^^^^

The `Thanzi la Onse model <https://github.com/UCL/TLOmodel>`_ repository, containing the source code for the simulation itself.

Source branch
^^^^^^^^^^^^^

The branch of this repository that contains the ``.pyisession`` files, which themselves are the results of profiling sessions run on the `model repository`_.

Currently, the source branch is named `results <https://github.com/UCL/TLOmodel-profiling/tree/results>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
