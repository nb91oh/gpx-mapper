from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, get_flashed_messages, json
from werkzeug.utils import secure_filename
import os
import sqlite3
import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import LineString
import math

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

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if not allowed_file(f.filename) == True:
            # todo: make this a javascript alert
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
        bounds = json.dumps([line.bounds[::-1][0:2], line.bounds[::-1][2:4]])
        geojson = json.dumps(gpd.GeoSeries([line]).__geo_interface__)

        return render_template('home.html', hikes = hikes, location = location, geojson = geojson, bounds = bounds)


@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    sql = """SELECT hikes.filename AS hike FROM (SELECT DISTINCT filename, upload_date FROM points) hikes;"""
    cursor.execute(sql)
    results = cursor.fetchall()
    hikes = []
    for row in results:
        hikes.append(row['hike'])
    if request.method == 'GET':
        return render_template('dashboard.html', hikes = hikes)
    if request.method == 'POST':
        selected_hike = request.form['hikes']
        sql = "SELECT * FROM points WHERE filename = ?"
        df = pd.read_sql(sql = sql, con = conn, params = (selected_hike,))
        avg_x = df.x.mean()
        avg_y = df.y.mean()
        epsg = latLong2ESPG(avg_y, avg_x)
        points_df = gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y, df.z))
        points_df = points_df.set_crs(epsg=4326)
        points_utm_df = points_df.to_crs(epsg=epsg)
        points = points_utm_df.geometry
        distances = []
        for i in list(range(len(points))):
            if i == 0:
                distance = 0
            else:
                x = (points[i].x - points[i-1].x) ** 2
                y = (points[i].y - points[i-1].y) ** 2
                distance = math.sqrt(x+y)
            distances.append(distance)
        total_distance = round(sum(distances)/1000, 2)
        return render_template('dashboard.html', hikes = hikes, distance = total_distance)
