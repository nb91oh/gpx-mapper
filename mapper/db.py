import sqlite3
import os

def create_db():
    if os.path.exists('./sqlite/gpx.db'):
        return
    conn = sqlite3.connect('./sqlite/gpx.db')
    with open('./sqlite/create.sql', 'r') as file:
        sql = file.read()
        commands = sql.split(';')
        for command in commands:
            conn.execute(command)
        conn.commit()
        conn.close()
    return 

if __name__ == "__main__":
    create_db()