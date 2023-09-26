Supporting ``GitPython`` functions
==================================

The codebase uses ``GitPython`` to fetch the files from the source branch containing profiling outputs.
This is necessary to avoid manually copying across files from the source branch every time we want to rebuild, avoid tracking the results files alongside the code that processes them, and to provide some buffer against the automatic workflow commit overwriting the ``main`` branch.

This has the added advantage that we can *read* files on the source branch one-at-a-time to minimise memory usage.

TODO: Write better docstrings. Also space some of this stuff out? No line breaks makes things look nasty :(

.. automodule:: git_tree
    :members:
    :undoc-members: