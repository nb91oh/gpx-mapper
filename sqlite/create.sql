CREATE TABLE points(
	filename text NOT NULL,
	hike_id TEXT NOT NULL,
	upload_date timestamp NOT NULL, 
	track_id text NOT NULL,
	segment_id text NOT NULL,
	point_id text NOT NULL,
	x real NOT NULL,
	y real NOT NULL,
	z real NOT NULL,
	created_at timestamp NOT NULL
	);

CREATE TABLE hikes(
	hike_id TEXT NOT NULL,
	hike_date TIMESTAMP NOT NULL,
	duration TIME NOT NULL,
	hike_length NUMERIC NOT NULL,
	elevation_gain NUMERIC NOT NULL,
	avg_speed NUMERIC NOT NULL
);
