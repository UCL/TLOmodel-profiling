# Thanzi la Onse

This is a repository for storing profiling outputs from the TLOmodel, an epidemiology modelling framework for the Thanzi la Onse project.
For more information about setting up, using, and running simulations using the model, [please see the main repository](https://github.com/UCL/TLOmodel) and information provided there.

## [Results Branch](https://github.com/UCL/TLOmodel-profiling/tree/results)

Profiling outputs are stored on the [`results` branch](https://github.com/UCL/TLOmodel-profiling/tree/results).
Results are organised into a tree structure named by `year/month/day/HHMM`, with the timestamp being that taken at the _start_ of the profiling run.

New results are pushed to this branch and are added to the tree structure.
Scripts on the `main` branch will pull information from this branch.
The rendered profiling results on the `gh-pages` branch pull information from this branch.