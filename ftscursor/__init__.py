"""This package contains a subclass of the sqlite3.Cursor class that makes
it easy to perform (simple) full-text-search operations using the sqlite3
module

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
