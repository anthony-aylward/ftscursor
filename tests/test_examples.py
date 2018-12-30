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


def test_validate_names(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    c.validate_table_name('posts')
    c.validate_column_names('posts', 'id', 'title', 'body')


def test_fts5(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'fts5')) == (1,)


def test_learn(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'learn SQLite')) == (1, 3)


def test_not(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'learn NOT text')) == (3,)


def test_or(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'learn OR text')) == (1, 2, 3)


def test_and(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'sqlite AND searching')) == (2,)


def test_precedence(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'search AND sqlite OR help')) == (1, 2, 3)


def test_paren(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    assert tuple(c.search('posts', 'search AND (sqlite OR help)')) == (1, 2)


def test_detach(example_connection):
    c = example_connection.cursor(factory=FTSCursor)
    c.detach_source_db()
