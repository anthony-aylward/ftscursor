#!/usr/bin/env python3
#===============================================================================
# example_script.py
#===============================================================================

"""An example script using the FTSCursor class"""




# Imports ======================================================================

import argparse
import sqlite3
from ftscursor import FTSCursor




# Functions ====================================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            'Create a sqlite3 FTS table in memory and perform a query'
        )
    )
    parser.add_argument(
        'db',
        metavar='<path/to/database.db>',
        help='a sqlite database'
    )
    parser.add_argument(
        'table',
        metavar='<table_name>',
        help='the table which will be indexed'
    )
    parser.add_argument(
        'columns',
        metavar='<column_name>',
        nargs='+',
        help='a column which will be indexed'
    )
    parser.add_argument(
        'query',
        metavar='<query>',
        help='a FTS query'
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    conn = sqlite3.connect(':memory:')
    c = conn.cursor(factory=FTSCursor)
    c.attach_source_db(args.db)
    c.validate_table_name(args.table)
    c.validate_column_names(args.table, *args.columns)
    c.index_all(args.table, args.columns)
    c.detach_source_db()
    print(tuple(c.search(args.table, args.query)))




# Execute ======================================================================

if __name__ == '__main__':
    main()
