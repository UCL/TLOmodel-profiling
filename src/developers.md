# Developer Documentation

The purpose of this repository is to provide a storage space for profiling runs performed on the [Thanzi la Onse model](https://github.com/UCL/TLOmodel), and a convenient way to page through the results that doesn't require developers to download the results for themselves.
The result is this repository, or specifically [the pages deployment](http://github-pages.ucl.ac.uk/TLOmodel-profiling).

Profiling session outputs, `.pyisession` files, are pushed from the [_model repository_](#model-repository) when the profiling workflow has completed to the [_source branch_](#source-branch).
This triggers the [`build-website`](https://github.com/UCL/TLOmodel-profiling/blob/main/.github/workflows/build-website.yaml) workflow which will run the [build script](#build-script).
This script will parse the files on the source branch, as well as update the developer docs with any changes, and deploy the new website over the old one.

On PRs, the profiling results HTML and developer docs HTML are required to build successfully before merging, however deployment only takes place when the `build-website` workflow is run on `main`, or triggered as a direct result of new profiling results being pushed.

## Build Steps

The build steps can be summarised as follows:
- Use [`doxygen`](https://www.doxygen.nl/) to build the developer docs; documenting the functions, classes, and scripts that perform the heavy lifting.
- Run the build script to process the profiling results:
  1. Scan the source branch for all `pyisession` files
  2. Render all profiling output files to HTML
  3. Process additional statistics that were pushed across with the profiling outputs, and produce plots.
  4. Write the [lookup table](profiling_index.md)
  5. Write the [run statistics](run_statistics.md)
  6. Include the index page in the build directory
- Combine the `doxygen` build and profiling results, and deploy to GitHub pages.

The build script makes use of a `pandas` DataFrame to keep track of the summary stats and the correspondence between `.pyisession` files and HTML outputs, for example.

### Contents of the source branch

Files on the source branch as assumed to have filenames in the following style:
```sh
{trigger}_{run_number}_{commit_sha}.pyisession
```
- `trigger`: The name of the `github.event` that triggered the profiling run.
- `run_number`: The `github.run_id` of the workflow that ran.
- `commit_sha`: The `github.sha` of the commit on which the profiling run was triggered.

In addition to the `pyisession` files, additional statistics that cannot be saved by the profiler (like the size of the final simulation population) can also be present on the source branch.
The additional statistics are assumed to be in `JSON` files that carry the same filename as their profiling output counterpart, but with the `.stats.json` extension.
These files are processed by the build script when producing the additional statistics page.
Additional statistics are not required to be present, as missing entries will be skipped or highlighted when rendering the corresponding page.


## Glossary of Terms

#### Build script

The python script that creates the HTML files that are deployed to GitHub pages.

This is the `website_build/build_site.py` script. 

#### Model repository

The [Thanzi la Onse model](https://github.com/UCL/TLOmodel) repository, containing the source code for the simulation itself.

#### Source branch

The branch of this repository that contains the `.pyisession` files, which themselves are the results of profiling sessions run on the [model repository](#model-repository).

Currently, the source branch is named [`results`](https://github.com/UCL/TLOmodel-profiling/tree/results).