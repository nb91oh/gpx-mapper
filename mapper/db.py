import sqlite3
import os

def create_db():
    if os.path.exists('./sqlite/gpx.db'):
        return
    conn = sqlite3.connect('./sqlite/gpx.db')
    with open('./sqlite/create.sql', 'r') as file:
        sql = file.read()
        conn.execute(sql)
    return 
