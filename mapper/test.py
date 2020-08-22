import sqlite3

sql = sqlite3.connect('./sqlite/gpx.db')
sql.row_factory = sqlite3.Row

cursor = sql.cursor()

cursor.execute("SELECT hikes.name || ' -- ' || hikes.filename AS hike, filename, name FROM (SELECT DISTINCT filename, name FROM points) hikes;")

result = cursor.fetchall()

for row in result:
    print(row['hike'])