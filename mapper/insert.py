import sqlite3
import gpxpy
import uuid
import datetime
import pandas as pd 
import geopandas as gpd
from shapely.geometry import LineString
import math


def parse_gpx(gpx_file):
    """parse a gpx file into points for insertion into db"""
    gpx = gpxpy.parse(gpx_file)
    points = []
    for track in gpx.tracks:
        track_id = uuid.uuid4()
        for segment in track.segments:
            segment_id = uuid.uuid4()
            for point in segment.points:
                point_id = uuid.uuid4()
                lat = point.latitude
                long = point.longitude
                elev = point.elevation
                time = point.time
                point = {"track_id": track_id, "segment_id": segment_id, "point_id": point_id, "lat": lat, "long": long, \
                        "elev": elev, "time": time}
                points.append(point)

    return points


def latLong2ESPG(lat, long):
    utm = (math.floor((long + 180)/6) % 60) + 1
    if lat >= 0:
        base_code = 32600
    else:
        base_code = 32700
    epsg = base_code + utm
    return epsg


def insert_gpx(conn, gpx_file):
    filename = gpx_file.filename

    cur = conn.cursor()
    select_sql = "SELECT * FROM points WHERE filename = ? LIMIT 1"
    cur.execute(select_sql, (filename,))
    result = cur.fetchall()
    if result:
        return

    points = parse_gpx(gpx_file)
    hike_id = uuid.uuid4()
    upload_date = datetime.datetime.now()

    insert_sql = "INSERT INTO points (filename, hike_id, upload_date, track_id, segment_id, point_id, x, y, z, created_at) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

    for i in points:
        conn.execute(insert_sql, (filename, str(hike_id), str(upload_date), str(i['track_id']), str(i['segment_id']), str(i['point_id']), i['long'], i['lat'], i['elev'], i['time']))

    df = pd.read_sql(con = conn, sql= 'SELECT hike_id, x, y, z, created_at FROM points WHERE hike_id = ?', params=(str(hike_id),))
    points_df = gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y, df.z))
    line = LineString(points_df.geometry)
    with open('./static/svg/{}.svg'.format(hike_id), 'w') as svg:
        svg.write(line._repr_svg_())

    points_df = points_df.set_crs(epsg = 4326)
    avg_x = points_df.x.mean()
    avg_y = points_df.y.mean()
    epsg = latLong2ESPG(avg_y, avg_x)
    points_df_utm = points_df.to_crs(epsg = epsg)

    line = LineString(points_df_utm.geometry)
    length_m = line.length

    start_time_str = points_df_utm.created_at[0].split('+')[0]
    end_time_str = list(points_df_utm.created_at)[-1].split('+')[0]
    hike_date = start_time_str.split(' ')[0]

    start_datetime = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    end_datetime = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

    total_time_seconds = (end_datetime - start_datetime).total_seconds()
    duration = str(datetime.timedelta(seconds = total_time_seconds))

    kmph = (length_m/1000)/(total_time_seconds/3600)

    elevations = list(points_df.z)

    total_gain = 0
    for i in list(range(len(elevations))):
        if i == 0:
            gain = 0
        gain = elevations[i] - elevations[i-1]
        if gain > 0:
            total_gain += gain

    insert_sql = "INSERT INTO hikes (hike_id, hike_date, duration, hike_length, elevation_gain, avg_speed) \
        VALUES (?, ?, ?, ?, ?, ?)"

    conn.execute(insert_sql, (str(hike_id), hike_date, duration, length_m, total_gain, kmph))
    conn.commit()
   
    return 

