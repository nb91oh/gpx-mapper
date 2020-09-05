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
    #sql.row_factory = sqlite3.Row
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
        hike = {"hike_id": hike_id, "hike_date": hike_date, "duration": duration, "hike_length": hike_length, "elevation_gain": elevation_gain, "avg_speed": avg_speed}
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

    return render_template('map.html', location = location, geojson = geojson, bounds = bounds)


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

    sql = """SELECT * FROM points \
        WHERE created_at = ? AND hike_id = ?\
        LIMIT 1;"""
    
    cursor.execute(sql, (utc_str_format, hike_id))
    results = cursor.fetchall()

    if results:
        return jsonify("the img was on this hike")
    else:
        return jsonify("the img was not on this hike")


