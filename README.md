# gpx-mapper
gpx-mapper is a flask application designed to allow users to upload .gpx files and view them as lines on a leaflet map

## installation
to run gpx_mapper you will need python and sqlite on your machine. first create a virtual environment at the root of the directory:

```
python3 -m venv venv
venv/source/activate
```

next, install the requirements:

```
pip install -r requirements.txt
```

## running the application

with the virtual environment activated and at the root of the directory run the following to start the application:

```
flask run
```

and navigate to http://127.0.0.1:5000/ to view the application


NOTE: this is in very early stages and very much a WIP :) 