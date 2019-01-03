#===============================================================================
# ftscursor.py
#===============================================================================

"""The FTSCursor class and related functions"""




# Imports ======================================================================

import sqlite3




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

    def attach_source_db(self, source_db_path, source_db_name='source'):
        """Attach a source database to the connection
        
        Parameters
        ----------
        source_db_path : str
            path to the source sqlite3 database file
        source_db_name : str, optional
            name for the source database, defaults to 'source'
        """

        self.execute('ATTACH ? AS ?', (source_db_path, source_db_name))
    
    def detach_source_db(self, source_db_name='source'):
        """Detach a source database from the connection
        
        Parameters
        ----------
        source_db_name : str, optional
            name of the source database, defaults to 'source'
        """

        self.execute('DETACH ?', (source_db_name,))

    def validate_table_name(self, table_name, source_db_name='source'):
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
        table_name,
        *column_names,
        source_db_name='source'
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
    
    def table_is_indexed(self, table_name):
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
    
    def indexed_columns(self, table_name):
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
    
    def source_table_has_id_column(self, table_name, source_db_name='source'):
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
        table,
        id,
        searchable,
        source_db_name='source',
        delete=True,
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
        table,
        searchable,
        source_db_name='source',
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
    
    def delete(self, table, id):
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
    
    def search(self, table, query):
        """Perform a search on an FTS table

        Parameters
        ----------
        table : str
            name of table to search in
        query : str
            SQL query string

        Returns
        -------
        tuple of int
            rowids of rows matching the query
        """

        self.validate_table_name(table, source_db_name='main')
        searchable_columns = self.indexed_columns(table)
        return tuple(
            tup[0] for tup in self.execute(
                f'SELECT rowid FROM {table} WHERE {table} MATCH ?',
                (' OR '.join(f'{col}:{query}' for col in searchable_columns),)
            )
        )




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
