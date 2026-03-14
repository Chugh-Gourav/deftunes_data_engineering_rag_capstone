SELECT
session_id,
user_id,
song_id,
artist_id,
session_start_time
from {{var("source_schema")}}.raw_sessions