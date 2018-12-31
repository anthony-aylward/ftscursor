"""A sqlite3 cursor with extra methods to support FTS3/4/5.

This package contains a subclass of the sqlite3.Cursor class that makes
it easy to perform (simple) full-text-search operations using the sqlite3
module.

See the included [example script](https://github.com/anthony-aylward/ftscursor/blob/master/ftscursor/example_script.py)
for an application of the FTSCursor class. Once `ftscursor` is installed, the
example script can be run from the command line by calling `ftscursor-example`.
For usage information, see `ftscursor-example -h`.

Classes
-------
FTSCursor
    A Cursor with additional methods to support FTS indexing & searching

Functions
---------
latest_fts_version
    Check the latest available FTS version, if any
"""

from ftscursor.ftscursor import latest_fts_version, FTSCursor
