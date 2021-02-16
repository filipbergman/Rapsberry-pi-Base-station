#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
testdbconn: Test MySQL Database Connection
"""
import sys
import MySQLdb

print(sys.version_info)   # Print Python version for debugging
print('--------------')
conn = None  # Database connection

try:
    # Open database connection.
    # Parameters are: (server_hostname, username, password, database_name, server_port=3306)
    conn = MySQLdb.connect('localhost', 'testuser', 'xxxx', 'testdb')
    print('Connected...')

    # Get a cursor from the connection, for traversing the records in result-set
    cursor = conn.cursor()

    # Execute a MySQL query via execute()
    cursor.execute('SELECT VERSION()')
    #cursor.execute('SELECT xxx')   # uncomment to trigger an exception

    # Fetch one (current) row into a tuple
    version = cursor.fetchone()
    print('Database version: {}'.format(version))  # one-item tuple

except MySQLdb.Error as e:
    print('error {}: {}'.format(e.args[0], e.args[1]))  # Error code number, description
    sys.exit(1)  # Raise a SystemExit exception for cleanup, but honor finally-block

finally:
    print('finally...')
    if conn:
        # Always close the connection
        conn.close()
        print('Closed...')
