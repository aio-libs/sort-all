========
sort-all
========

Sort ``__all__`` lists alphabetically

Usage
=====

Install the package, e.g. ``pip install sort-all <path-to-file>``

Run the tool: ``sort-all``

Command line options
====================

Options::

   usage: sort-all [-h] [--check] [--no-error-on-fix] [filenames ...]

   Sort __all__ records alphabetically.

   positional arguments:
     filenames          Files to process

   options:
     -h, --help         show this help message and exit
     --check            check the file for unsorted / unformatted imports and print them to the command line without modifying the file; return 0
                     when nothing would change and return 1 when the file would be reformatted.
     --no-error-on-fix  return 0 even if errors are occurred during processing files


Usage with pre-commit
=====================


sort-all can be used as a hook for pre-commit_.

To add sort-all as a plugin, add this repo definition to your configuration:

.. code-block:: yaml
   repos:
   - repo: https://github.com/aio-libs/sort-all
     rev: ...  # select the tag or revision you want, or run `pre-commit autoupdate`
     hooks:
     - id: sort-all

.. _`pre-commit`: https://pre-commit.com
