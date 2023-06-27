import sqlite3 as sql
import csv
from sqlite3 import Error


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sql.connect(db_file)
        print(sql.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    create_table()

def create_table():
    con = sql.connect('prikaway.db')
    cur = con.cursor()
    cur.execute("create table if not exists products(id int, item_name varchar(55), item_price int)")
    cur.execute("create table if not exists sales (roll_no int, student_name varchar(50), class int, house varchar(10), item_id int, item_purchased varchar(55), item_size varchar(5), item_quantity int, total_price int, tc_leave boolean, date_of_purchase date, bill_no varchar(20))")
    file = open('products.csv')
    contents = csv.reader(file)
    insert_records = "INSERT INTO products (id, item_name, item_price) VALUES(?, ?, ?)"
    cur.executemany(insert_records, contents)
    con.commit()
    con.close()

if __name__ == '__main__':
    create_connection(r"prikaway.db")