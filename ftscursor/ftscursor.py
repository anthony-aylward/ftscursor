#===============================================================================
# ftscursor.py
#===============================================================================

"""The FTSCursor class and related functions"""




# Imports ======================================================================

import math
import sqlite3
import sys



# Classes ======================================================================

class FTSCursor(sqlite3.Cursor):
    """A Cursor with additional methods to support FTS indexing & searching

    Attributes
    ----------
    default_fts_version : int
        The default FTS version used for table creation. It is the value
        returned by `latest_fts_version()`.
    """

    def __init__(self, *args, **kwargs):
        """Set the default FTS version and perform normal Cursor initialization
        """

        self.default_fts_version = latest_fts_version()
        super().__init__(*args, **kwargs)

    def attach_source_db(
        self,
        source_db_path: str,
        source_db_name: str = 'source'
    ):
        """Attach a source database to the connection
        
        Parameters
        ----------
        source_db_path : str
            path to the source sqlite3 database file
        source_db_name : str, optional
            name for the source database, defaults to 'source'
        """

        self.execute('ATTACH ? AS ?', (source_db_path, source_db_name))
    
    def detach_source_db(self, source_db_name: str ='source'):
        """Detach a source database from the connection
        
        Parameters
        ----------
        source_db_name : str, optional
            name of the source database, defaults to 'source'
        """

        self.execute('DETACH ?', (source_db_name,))

    def validate_table_name(
        self,
        table_name: str,
        source_db_name: str = 'source'
    ):
        """Check that a database contains a table with the provided name

        Parameters
        ----------
        table_name : str
            table name to check
        source_db_name : str, optional
            name of the source database, defaults to 'source'

        Raises
        ------
        ValueError
            if no table with the provided name exists in the source database
        """

        if table_name not in {
            tup[0] for tup in self.execute(
                f"SELECT name FROM {source_db_name}.sqlite_master "
                "WHERE type='table'"
            )
        }:
            raise ValueError('Invalid table name')
    
    def validate_column_names(
        self,
        table_name: str,
        *column_names: str,
        source_db_name: str ='source'
    ):
        """Check that a table includes the provided columns

        Parameters
        ----------
        table_name : str
            table name to check
        *column_names : str
            column names to check
        source_db_name : str, optional
            name of the source database, defaults to 'source'

        Raises
        ------
        ValueError
            if the provided columns are not a subset of the table's columns
        """

        self.execute(f'SELECT * FROM {source_db_name}.{table_name}')
        if not set(column_names) <= {tup[0] for tup in self.description}:
            raise ValueError('Invalid column names')
    
    def table_is_indexed(self, table_name: str):
        """Check that a FTS table with the provided name has been created

        Parameters
        ----------
        table_name : str
            table name to check

        Returns
        -------
        bool
            True if a FTS table with the provided name exists, False otherwise
        """
        return table_name in {
            tup[0] for tup in self.execute(
                "SELECT name FROM main.sqlite_master WHERE type='table'"
            )
        }
    
    def indexed_columns(self, table_name: str):
        """List the columns of a FTS table

        Parameters
        ----------
        table_name : str
            name of a FTS table

        Returns
        -------
        tuple of str
            names of columns in the provided table
        """

        self.execute(f'SELECT * FROM main.{table_name}')
        return tuple(tup[0] for tup in self.description)
    
    def source_table_has_id_column(
        self,
        table_name: str,
        source_db_name: str = 'source'
    ):
        """Check whether or not a table in the source db has an "id" column

        Parameters
        ----------
        table_name : str
            table name to check

        Returns
        -------
        bool
            True if the source table has an "id" column, False otherwise
        """

        self.execute(f'SELECT * FROM {source_db_name}.{table_name}')
        return 'id' in set(tup[0] for tup in self.description)
    
    def index(
        self,
        table: str,
        id: int,
        searchable,
        source_db_name: str = 'source',
        delete: bool = True,
        fts_version=None
    ):
        """Add a row to a FTS table, creating a new table if necessary
        
        Parameters
        ----------
        table : str
            name of the table in the source database
        id : int
            rowid of the row to index in the source database
        searchable : iterable of str
            column names to include in the FTS table
        source_db_name : str, optional
            name of the source database, defaults to 'source'
        delete : bool
            if True, perform a delete operation to remove an existing row
            with the same rowid before adding the new row
        fts_version : int
            FTS version to use if a new table is created
        """

        self.validate_table_name(table, source_db_name=source_db_name)
        self.validate_column_names(
            table,
            *searchable,
            source_db_name=source_db_name
        )
        has_id_column = not self.source_table_has_id_column(
            table,
            source_db_name=source_db_name
        )
        if not self.table_is_indexed(table):
            self.execute(f"""
                CREATE VIRTUAL TABLE {table}
                USING fts{
                    fts_version if fts_version else self.default_fts_version
                }({', '.join(searchable)})
                """
            )
        if delete:
            self.execute(f'DELETE FROM {table} WHERE rowid = ?', (id,))
        self.execute(f"""
            INSERT INTO {table}(rowid, {', '.join(searchable)})
            SELECT {'row' * (not has_id_column)}id, {', '.join(searchable)}
            FROM {source_db_name}.{table}
            WHERE {'row' * (not has_id_column)}id = ?
            """,
            (id,)
        )
    
    def index_all(
        self,
        table: str,
        searchable,
        source_db_name: str = 'source',
        fts_version=None
    ):
        """Create a new FTS table by copying an existing table in the source
        database
        
        Parameters
        ----------
        table : str
            name of the table in the source database
        searchable : iterable of str
            column names to include in the FTS table
        source_db_name : str, optional
            name of the source database, defaults to 'source'
        fts_version : int
            FTS version to use if a new table is created
        """

        self.validate_table_name(table, source_db_name=source_db_name)
        self.validate_column_names(
            table,
            *searchable,
            source_db_name=source_db_name
        )
        if self.table_is_indexed(table):
            raise RuntimeError(f'A FTS table named {table} already exists')
        self.executescript(f"""
            CREATE VIRTUAL TABLE {table}
            USING fts{fts_version if fts_version else self.default_fts_version}(
                {', '.join(searchable)}
            );

            INSERT INTO {table}(rowid, {', '.join(searchable)})
            SELECT id, {', '.join(searchable)}
            FROM {source_db_name}.{table}
            """
        )
    
    def delete(self, table: str, id: int):
        """Delete a row from a FTS table

        Parameters
        ----------
        table : str
            name of table to delete from
        id : int
            rowid of row to delete
        """

        self.validate_table_name(table, source_db_name='main')
        self.execute(f'DELETE FROM {table} WHERE rowid = ?', (id,))
    
    def search(self, table: str, query: str, fts_version=None):
        """Perform a search on an FTS table

        Parameters
        ----------
        table : str
            name of table to search in
        query : str
            SQL query string
        fts_version
            The FTS version to use (4 or 5)

        Returns
        -------
        tuple of int
            rowids of rows matching the query, sorted by relevance
        """

        if fts_version == None:
            fts_version = self.default_fts_version
        self.validate_table_name(table, source_db_name='main')
        searchable_columns = self.indexed_columns(table)
        q = (' OR '.join(f'{col}:{query}' for col in searchable_columns),)
        if fts_version == 5:
            return tuple(
                tup[0] for tup in self.execute(f'''
                    SELECT rowid FROM {table} WHERE {table} MATCH ? ORDER BY
                    rank
                    ''',
                    q
                )
            )
        else:
            return tuple(
                tup[0] for tup in self.execute(f'''
                    SELECT rowid, matchinfo({table}, 'pcnalx') FROM {table}
                    WHERE {table} MATCH ?
                    ''',
                    q
                ).sorted(key=lambda tup: _bm25(*_parse_matchinfo(tup[1])))
            )


    def drop(self, table: str):
        """Drop a FTS table

        Parameters
        ----------
        table : str
            name of table to drop
        """

        self.validate_table_name(table, source_db_name='main')
        self.execute(f'DROP TABLE {table}')




# Functions ====================================================================

def latest_fts_version():
    """Check for the latest available FTS version, if any

    Returns
    -------
    int
        5 if FTS5 is the latest available FTS version, 4 if FTS3/4 is the latest

    Raises
    ------
    RuntimeError
        if no FTS extensions are enabled
    """

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('pragma compile_options')
    available_pragmas = c.fetchall()
    conn.close()
    if ('ENABLE_FTS5',) in available_pragmas:
        return 5
    if ('ENABLE_FTS3',) in available_pragmas:
        return 4
    raise RuntimeError('FTS extensions are not enabled')

def _chunks(s, n):
    for i in range(0, len(s), n):
        yield s[i:i + n]

def _parse_matchinfo(matchinfo):
    n_phrases, n_columns, n_rows, *rest = (
        int.from_bytes(x, byteorder=sys.byteorder)
        for x in _chunks(matchinfo, 4)
    )
    avg_tokens, n_tokens, x = (
        rest[0:n_columns],
        rest[n_columns:(2 * n_columns)],
        tuple(_chunks(_chunks(rest[(2 * n_columns):], 3), n_columns))
    )
    return n_phrases, n_columns, n_rows, avg_tokens, n_tokens, x

def _inverse_document_frequency(n_rows, n_match):
    return math.log(n_rows - n_match + 0.5) - math.log(n_match + 0.5)

def _bm25(n_phrases, n_columns, n_rows, avg_tokens, n_tokens, x):
    k = 1.2
    b = 0.75
    inverse_document_freq = tuple(
        tuple(
            _inverse_document_frequency(n_rows, x[phrase][col][3])
            for phrase in range(n_phrases)
        )
        for col in range(n_columns)
    )
    phrase_freq = tuple(
        tuple(x[phrase][col][1] for phrase in range(n_phrases))
        for col in range(n_columns)
    )
    return -1 * sum(
        idf * f * (k + 1) / (
            f + k * (1 - b + b * n_tokens[col] / avg_tokens[col])
        )
        for col in range(n_columns)
        for idf, f in zip(inverse_document_freq[col], phrase_freq[col])
    )
