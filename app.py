from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3

from mapper.map import get_map
from mapper.db import create_db
from mapper.insert import insert_gpx


app = Flask(__name__)

app.secret_key = 'ishouldreallychangethis'

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = ['gpx']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    sql = """SELECT hikes.name || ' -- ' || hikes.filename AS hike FROM (SELECT DISTINCT filename, name FROM points) hikes;"""
    cursor.execute(sql)
    results = cursor.fetchall()
    data = []
    for row in results:
        data.append(list(row))
    return jsonify(data)
    # path = './uploads'
    # files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    # if len(files) == 0:
    #     return "<h1>this is the home page</h1>"
    # else:
    #     return str(files)

@app.route('/index')
def index():
    m = get_map()
    return m

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if not allowed_file(f.filename) == True:
            return "sorry we only take .gpx round these parts"
        user_text = request.form.get('name')
        conn = get_db()
        insert_gpx(conn, f, user_text)
        # f.save(os.path.join('uploads', secure_filename(f.filename)))
        flash('file uploaded successfully')
        return redirect(url_for('home'))
