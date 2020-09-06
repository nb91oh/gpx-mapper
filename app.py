from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, get_flashed_messages, json
from werkzeug.utils import secure_filename
import os
import sqlite3
import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import LineString
import math
import exifread
import datetime
import pytz
from tzwhere import tzwhere
from pytz import timezone
import pytz
import uuid

from mapper.db import create_db
from mapper.insert import insert_gpx


app = Flask(__name__)

app.secret_key = 'ishouldreallychangethis'

ALLOWED_EXTENSIONS = ['gpx']


create_db()

def allowed_file(filename):
    if filename.split('.')[-1] not in ALLOWED_EXTENSIONS:
        return False
    else:
        return True

def connect_db():
    sql = sqlite3.connect('./sqlite/gpx.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def latLong2ESPG(lat, long):
    utm = (math.floor((long + 180)/6) % 60) + 1
    if lat >= 0:
        base_code = 32600
    else:
        base_code = 32700
    espg = base_code + utm
    return espg

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/uploader', methods = ['POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        # if not allowed_file(f.filename) == True:
        #     # todo: make this a javascript alert
        #     flash("sorry we only take .gpx round these parts")
        #     return redirect(url_for('upload'))
        for file in files:
            conn = get_db()
            insert_gpx(conn, file)
        return redirect(url_for('test'))


@app.route('/')
def test():
    conn = get_db()
    cursor = conn.cursor()
    sql = """SELECT DISTINCT hike_id, hike_date, duration, hike_length, elevation_gain, avg_speed FROM hikes ORDER BY hike_date;"""
    cursor.execute(sql)
    results = cursor.fetchall()
    hikes = []
    for row in results:

        
        hike_id = row['hike_id']
        hike_date = row['hike_date']
        duration = row['duration']
        hike_length = row['hike_length']
        elevation_gain = row['elevation_gain']
        avg_speed = row['avg_speed']

        sql = "SELECT count() as count FROM images WHERE hike_id = ? ;"
        cursor.execute(sql, (hike_id,))
        result = cursor.fetchall()
        image_count = result[0]['count']
        hike = {"hike_id": hike_id, "hike_date": hike_date, "duration": duration,
                "hike_length": hike_length, "elevation_gain": elevation_gain, "avg_speed": avg_speed,
                "image_count": image_count}
        hikes.append(hike)

    return render_template('home.html', hikes = hikes)

@app.route('/map')
def map():
    conn = get_db()
    hike_id = request.args.get('id')
    sql = "SELECT hike_points.x, hike_points.y FROM (SELECT * FROM points WHERE hike_id = ? ORDER BY created_at ASC) hike_points"
    df = pd.read_sql(sql = sql, con = conn, params = (hike_id,))
    points_df = gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y))
    line = LineString(points_df.geometry)
    center_x = line.centroid.x
    center_y = line.centroid.y
    location = json.dumps([center_y, center_x])
    bounds = json.dumps([line.bounds[::-1][0:2], line.bounds[::-1][2:4]])
    geojson = json.dumps(gpd.GeoSeries([line]).__geo_interface__)

    sql = """
WITH p AS (
	SELECT point_id, image_id 
	FROM images 
	WHERE hike_id = ?
)
SELECT p.point_id, p.image_id, points.x, points.y FROM points
INNER JOIN p ON points.point_id = p.point_id
    """

    cur = conn.cursor()
    cur.execute(sql, (hike_id,))
    result = cur.fetchall()
    markers = []
    for row in result:
        image_id = row['image_id']
        x = row['x']
        y = row['y']
        marker = {"image_id": image_id, "x": x, "y": y}
        markers.append(marker)

    return render_template('map.html', location = location, geojson = geojson, bounds = bounds, markers = markers)


@app.route('/img_upload', methods = ['POST'])
def img_upload():
    for file in request.files:
        if file.startswith('img_file'):
            hike_id = file.split('.')[1]

    f = request.files[f'img_file.{hike_id}']

    tags = exifread.process_file(f)
    datetimestr = tags['Image DateTime'].values
    datetimeobj = datetime.datetime.strptime(datetimestr, "%Y:%m:%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    sql = "SELECT AVG(y) , AVG(x) FROM points WHERE hike_id = ?"
    cursor.execute(sql, (hike_id,))
    results = cursor.fetchone()
    avg_y = results[0]
    avg_x = results[1]
    tz = tzwhere.tzwhere()
    timezone_str = tz.tzNameAt(avg_y, avg_x)
    
    fmt = '%Y-%m-%d %H:%M:%S%z'
    eastern = timezone(timezone_str)
    loc_dt = eastern.localize(datetimeobj)
    utc = pytz.utc
    utc_str = loc_dt.astimezone(utc).strftime(fmt)
    utc_str_format = utc_str[:-2] + ':' '00'

    sql = """SELECT hike_id, point_id FROM points \
        WHERE created_at = ? AND hike_id = ?\
        LIMIT 1;"""
    
    cursor.execute(sql, (utc_str_format, hike_id))
    results = cursor.fetchall()

    image_id = str(uuid.uuid4())
    f.save(f"./static/img/{image_id}.jpg")

    hike_id = results[0]['hike_id']
    point_id = results[0]['point_id']

    sql = "INSERT INTO images (image_id, point_id, hike_id) VALUES (?, ?, ?);"

    conn.execute(sql, (image_id, point_id, hike_id))
    conn.commit()

    return redirect(url_for('test'))

    




