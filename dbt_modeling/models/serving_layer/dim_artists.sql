SELECT
artist_id,
MAX(artist_mbid) AS artist_mbid,
MAX(artist_name) AS artist_name
FROM {{var("source_schema")}}.raw_songs
GROUP BY artist_id