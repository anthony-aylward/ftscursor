# ftscursor
A sqlite3 cursor with extra methods to support FTS3/4/5.

This package contains a subclass of the sqlite3.Cursor class that makes
it easy to perform (simple) full-text-search operations using the sqlite3
module.

See the included [example script](https://github.com/anthony-aylward/ftscursor/blob/master/ftscursor/example_script.py)
for an application of the FTSCursor class. Once `ftscursor` is installed, the
example script can be run from the command line by calling `ftscursor-example`.
For usage information, see `ftscursor-example -h`:

```
usage: ftscursor-example [-h]
                         <path/to/database.db> <table_name> <column_name>
                         [<column_name> ...] <query>

Create a sqlite3 FTS table in memory and perform a query

positional arguments:
  <path/to/database.db>
                        a sqlite database
  <table_name>          the table which will be indexed
  <column_name>         a column which will be indexed
  <query>               a FTS query

optional arguments:
  -h, --help            show this help message and exit
```