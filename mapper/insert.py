import sqlite3
import gpxpy
import uuid
import datetime

def parse_gpx(gpx_file):
    # todo : write the logic to parse the gpx file
    # should return list of list of track/segment/point/x/y/z/time
    
    gpx =  gpxpy.parse(gpx_file)

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

def insert_gpx(conn, gpx_file, user_text):
    insert_sql = "INSERT INTO points (filename, name, upload_date, track_id, segment_id, point_id, x, y, z, created_at) \
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

    filename = gpx_file.filename
    points = parse_gpx(gpx_file)
    upload_date = datetime.datetime.now()

    for i in points:
        conn.execute(insert_sql, (filename, user_text, str(upload_date), str(i['track_id']), str(i['segment_id']), str(i['point_id']), i['long'], i['lat'], i['elev'], i['time']))
    conn.commit()
    return 