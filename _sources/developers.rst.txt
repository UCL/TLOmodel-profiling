Developer Documentation
=======================

- :ref:`Build steps <developers:build steps>`
- :ref:`Triggering a build <developers:triggering a build>`
- :ref:`Contents of the Source Branch <developers:contents of the source branch>`
- :ref:`Glossary <developers:glossary of terms>`

See also the :doc:`API Reference <api-reference>` for detailed code use.

Overview
--------

The purpose of this repository is to provide a storage space for profiling runs performed on the `Thanzi la Onse model <https://github.com/UCL/TLOmodel>`_, and a convenient way to page through the results that doesn't require developers to download the results for themselves.
The result is this repository, or specifically `the pages deployment <http://github-pages.ucl.ac.uk/TLOmodel-profiling>`_.

Profiling session outputs, ``.pyisession`` files, are pushed from the `model repository`_ when the profiling workflow has completed to the `source branch`_.
This triggers the `build-website <https://github.com/UCL/TLOmodel-profiling/blob/main/.github/workflows/build-website.yaml>`_ workflow which will run the `build script`_.
This script will parse the files on the `source branch`_, as well as update the developer docs with any changes, and deploy the new website over the old one.

On PRs, the profiling results HTML and developer docs HTML are required to build successfully before merging, however deployment only takes place when the ``build-website`` workflow is run on ``main``, or triggered as a direct result of new profiling results being pushed.

Triggering a build
------------------

The build can be triggered by passing the ``website_builder/builder.py`` script to a Python interpreter with the requirements installed;

.. code-block:: bash

   python website_builder/builder.py

You may pass the ``-h`` or ``--help`` flags for the command line help, which provides a few convenience wrappers for the :class:`builder.Builder` class that manages the website build.
Configuration options include specifying a particular directory to place the built website into, forcing the removal of any previously (failed or completed) builds, and toggling the structure of static HTML files from profiling outputs into a flat directory or nested directory structure.

The API to the class can also be used to trigger builds - see the :doc:`corresponding API reference <api/builder>` for more information.

Build Steps
-----------

The website consists of two parts:

* The profiling results and statistics, which are created by the scripts in ``website_builder``, the results stored on the `source branch`_, and the content of the ``source`` folder.
* The developer documentation, which is created from the content of the ``source`` folder.

The website is built using `sphinx <https://www.sphinx-doc.org/en/master/index.html>`_, which is invoked at the end of the ``website_builder/builder.py`` script (specifically within the :class:`builder.Builder.build()` method).
Before ``sphinx-build`` can be invoked, the profiling results on the `source branch`_ need to be parsed.
As such, the :class:`builder.Builder` first creates a *staging* directory, and copies the content of the ``source`` directory content into it as a starting point.

Files are then added to the staging directory as they are processed from the source branch; these additions consist primarily of profiling sessions that have been rendered as HTML, and plots for displaying runtime statistics.
The statistics files from the profiling runs are not copied across from the source branch - they are instead read into the :class:`builder.Builder.df` ``DataFrame``.
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

:class:`builder.Builder.df` keeps track of the summary stats and the correspondence between ``.stats.json`` files and HTML outputs.

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