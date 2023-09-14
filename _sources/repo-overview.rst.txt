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

* The profiling results and statistics, which are created by the scripts in ``website_builder`` and the results stored on the `source branch`_.
* The developer documentation, which is created from the content of the ``source`` folder.

The website is built using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`_, which is invoked at the end of the ``website_builder/build_site.py`` script (specifically within the ``WebsiteBuilder.build()`` method).
Before ``sphinx-build`` can be invoked, the profiling results on the `source branch`_ need to be parsed.
As such, the ``WebsiteBuilder`` first creates a *pre-build* directory, and copies the content of the ``source`` directory content into it as a starting point.
Files are then added to the pre-build directory as they are processed from the source branch; these additions consist primarily of ``pyinstrumment`` sessions rendered as HTML, and plots for displaying runtime statistics.
Lookup tables for profiling runs are also generated in this phase, and their content is inserted into the placeholder locations in the `profiling.rst` and `run-statistics.rst` files in the pre-build directory.
Having done this pre-build step, ``sphinx`` will be invoked on the pre-build directory to build the HTML content of the website, creating the ``build`` directory with the HTML to be deployed.

An overview of the steps in the ``build_site.py`` script is provided below:

#. Copy the ``source`` directory into the pre-build directory.
#. Scan the source branch for all ``.pyisession`` files.
#. Render all profiling output files to HTML.
#. Process additional statistics that were pushed across with the profiling outputs, and produce plots.
#. Write the lookup table to ``profiling.rst``.
#. Write the run statistics to ``run_statistics.rst``.
#. Invoke ``sphinx-build`` on the pre-build directory to create the website.

The build script makes use of a ``pandas`` DataFrame to keep track of the summary stats and the correspondence between ``.pyisession`` files and HTML outputs.

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