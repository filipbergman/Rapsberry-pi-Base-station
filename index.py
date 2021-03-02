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

def print_list():
    conn = MySQLdb.connect('localhost', 'pi', 'pi', 'dbtest')
    global lh

    file1 = open('/var/www/mypython-test/values.txt', 'r')
    Lines = file1.readlines()
    #print("LINES: ", Lines)

    for line in Lines:
        #print("Line: ", line)
        li = list(line.split(","))
        #print("LINE LIST: ", li)
        cursor.execute("insert into cafe (category, name, price) values (%s, %s, %s)", (li))

    conn.commit()

    # Query all records
    cursor.execute('select * from cafe')
    rows = cursor.fetchall()
    for row in rows:
        print('<p>' + str(row) + '</p>')   # Print HTML paragraphs
    conn.close()    

def commit_line():
    global value_list
    global lh
    # TODO: add new values to a list, then instead print the list in execute
    with open("/var/www/mypython-test/values.txt","a") as f:
        f.write("tea,33,3.19\n")
        f.write("tea,33,3.19\n")

cursor = conn.cursor()
# Create table
cursor.execute('drop table if exists cafe')
cursor.execute('''create table if not exists cafe (
                    id int unsigned not null auto_increment,
                    category enum('tea', 'coffee') not null,
                    name varchar(50) not null,
                    price varchar(50) not null,
                    primary key (id)
                  )''')
# Insert rows
print_list()