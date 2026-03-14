SELECT
song_id,
artist_id,
track_id,
title,
release,
year
from {{var("source_schema")}}.raw_songs