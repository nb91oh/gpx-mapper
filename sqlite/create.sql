CREATE TABLE points(
	filename text NOT NULL,
	upload_date timestamp NOT NULL, 
	track_id text NOT NULL,
	segment_id text NOT NULL,
	point_id text NOT NULL,
	x real NOT NULL,
	y real NOT NULL,
	z real NOT NULL,
	created_at timestamp NOT NULL
	);