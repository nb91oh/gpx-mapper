from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, get_flashed_messages, json
from werkzeug.utils import secure_filename
import os
import sqlite3
import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import LineString

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


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if not allowed_file(f.filename) == True:
            flash("sorry we only take .gpx round these parts")
            return redirect(url_for('upload'))
        conn = get_db()
        insert_gpx(conn, f)
        return redirect(url_for('index'))


@app.route('/', methods = ['GET', 'POST'])
def index():
    conn = get_db()
    cursor = conn.cursor()
    sql = """SELECT hikes.filename AS hike FROM (SELECT DISTINCT filename, upload_date FROM points) hikes;"""
    cursor.execute(sql)
    results = cursor.fetchall()
    hikes = []
    for row in results:
        hikes.append(row['hike'])
    if request.method == 'GET':
        return render_template('home.html', hikes=hikes)
    elif request.method == 'POST':
        selected_hike = request.form['hikes']
        sql = "SELECT hike_points.x, hike_points.y, hike_points.z FROM (SELECT * FROM points WHERE filename = ? ORDER BY created_at ASC) hike_points"
        df = pd.read_sql(sql = sql, con = conn, params = (selected_hike,))
        points_df = gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y))
        line = LineString(points_df.geometry)
        center_x = line.centroid.x
        center_y = line.centroid.y
        location = json.dumps([center_y, center_x])
        geojson = json.dumps(gpd.GeoSeries([line]).__geo_interface__)

        return render_template('home.html', hikes = hikes, location = location, geojson = geojson)
