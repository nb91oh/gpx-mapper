import sqlite3
import pandas as pd

sql = sqlite3.connect('./sqlite/gpx.db')
sql.row_factory = sqlite3.Row

cursor = sql.cursor()

cursor.execute("SELECT hikes.name AS hike FROM (SELECT DISTINCT filename, name FROM points) hikes;")

result = cursor.fetchall()

hikes = []

for row in result:
    hikes.append(row['hike'])

example_hike = (hikes[0])


query = "SELECT hike_points.x, hike_points.y, hike_points.z FROM (SELECT * FROM points WHERE name = ? ORDER BY created_at ASC) hike_points"

df = pd.read_sql(sql = query, con = sql, params = (example_hike,))

