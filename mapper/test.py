import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import geopandas as gpd
import folium

def get_map():
    load_dotenv()
    pgpass = os.getenv('pgpass')
    conn = psycopg2.connect(user = "postgres", 
                            password = pgpass,
                            host = "127.0.0.1",
                            port = 5432,
                            database = "gpx")
    sql = "SELECT * FROM lines"
    gdf = gpd.read_postgis(sql, conn)
    line = gdf.geom[2]
    geojson = line.__geo_interface__
    center_x = line.centroid.x
    center_y = line.centroid.y
    m = folium.Map(location=[center_y, center_x], zoom_start=12)
    folium.GeoJson(
        geojson,
        name = 'geojson',
    ).add_to(m)

    return m._repr_html_()

m = get_map()

with open("test.html", "w") as file:
    file.write(m)
