import pytest
import sqlite3
import tempfile
from ftscursor import FTSCursor

@pytest.fixture(scope="module")
def example_connection():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor(factory=FTSCursor)
    c.attach_source_db(':memory:')
    c.executescript('''
        CREATE TABLE source.posts(id INTEGER, title TEXT, body TEXT);
        INSERT INTO posts(id, title, body)
        VALUES
        (1, 'Learn SQlite FTS5', 'This tutorial teaches you how to perform full-text search in SQLite using FTS5'),
        (2, 'Advanced SQlite Full-text Search', 'Show you some advanced techniques in SQLite full-text searching'),
        (3, 'SQLite Tutorial', 'Help you learn SQLite quickly and effectively');
        '''
    )
    c.index_all('posts', ('title', 'body'))
    return conn

def test_drop(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    c.drop('posts')