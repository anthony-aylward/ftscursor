#===============================================================================
# ftscursor.py
#===============================================================================

# Imports ======================================================================

from sqlite3 import Cursor




# Classes ======================================================================

class FTSCursor(Cursor):
    """A Cursor with additional methods to support FTS indexing & searching"""

    def attach_source_db(self, source_db_path, source_db_name='source'):
        self.execute('ATTACH ? AS ?', (source_db_path, source_db_name))
    
    def detach_source_db(self, source_db_name='source'):
        self.execute('DETACH ?', (source_db_name,))

    def validate_table_name(self, table_name, source_db_name='source'):
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
        self.execute(f'SELECT * FROM {source_db_name}.{table_name}')
        if not set(column_names) <= {tup[0] for tup in self.description}:
            raise ValueError('Invalid column names')
    
    def table_is_indexed(self, table_name):
        return table_name in {
            tup[0] for tup in self.execute(
                "SELECT name FROM main.sqlite_master WHERE type='table'"
            )
        }
    
    def indexed_columns(self, table_name):
        self.execute(f'SELECT * FROM main.{table_name}')
        return tuple(tup[0] for tup in self.description)
    
    def index(
        self,
        table,
        id,
        searchable,
        source_db_name='source',
        delete=True,
        fts_version=4
    ):
        self.validate_table_name(table, source_db_name=source_db_name)
        self.validate_column_names(
            table,
            *searchable,
            source_db_name=source_db_name
        )
        if not self.table_is_indexed(table):
            self.execute(f"""
                CREATE VIRTUAL TABLE {table}
                USING fts{fts_version}({', '.join(searchable)})
                """
            )
        if delete:
            self.execute(f'DELETE FROM {table} WHERE docid = ?', (id,))
        self.execute(f"""
            INSERT INTO {table}(docid, {', '.join(searchable)})
            SELECT id, {', '.join(searchable)}
            FROM {source_db_name}.{table}
            WHERE id = ?
            """,
            (id,)
        )
    
    def delete(self, table, id):
        self.validate_table_name(table, source_db_name='main')
        self.execute(f'DELETE FROM {table} WHERE id = ?', (id,))
    
    def search(
        self,
        table,
        query,
        page,
        per_page,
        source_db_name='source'
    ):
        self.validate_table_name(table, source_db_name=source_db_name)
        searchable_columns = self.indexed_columns(table)
        return tuple(
            tup[0] for tup in self.execute(
                f'SELECT docid FROM {table} WHERE {table} MATCH ?',
                (' OR '.join(f'{col}:{query}' for col in searchable_columns),)
            )
        )