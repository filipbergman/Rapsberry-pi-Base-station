#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index: Test home page
"""
# Turn on debug mode to show the error message. To disable for production.
import cgitb
cgitb.enable()

# Print HTML response header, followed by a new line
print("Content-Type: text/html\n")

# For MySQL
import MySQLdb
conn = MySQLdb.connect('localhost', 'pi', 'pi', 'dbtest')
# For PostgreSQL
#import psycopg2
#conn = psycopg2.connect(database='testdb', user='testuser', password='xxxx', host='localhost', port='5432')

with conn:
    cursor = conn.cursor()
    # Create table
    cursor.execute('drop table if exists cafe')
    cursor.execute('''create table if not exists cafe (
                        id int unsigned not null auto_increment,
                        category enum('tea', 'coffee') not null,
                        name varchar(50) not null,
                        price decimal(5,2) not null,
                        primary key (id)
                      )''')
    # Insert rows
    cursor.execute('''insert into cafe (category, name, price) values
                        ('coffee', 'Espresso', 3.19),
                        ('coffee', 'Cappuccino', 3.29),
                        ('coffee', 'Caffe Latte', 3.39),
                        ('tea', 'Green Tea', 2.99),
                        ('tea', 'Wulong Tea', 2.89)''')
    # Commit the insert
    conn.commit()

    # Query all records
    cursor.execute('select * from cafe')
    rows = cursor.fetchall()
    for row in rows:
        print('<p>' + str(row) + '</p>')   # Print HTML paragraphs
