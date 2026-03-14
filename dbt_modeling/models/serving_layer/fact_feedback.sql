SELECT
feedback_id,
user_id,
song_id,
action,
timestamp
from {{var("source_schema")}}.raw_user_feedback
