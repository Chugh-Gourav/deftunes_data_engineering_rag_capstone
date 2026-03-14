SELECT
EXTRACT(YEAR FROM ff.timestamp) AS interaction_year,
da.artist_name,
ff.action,
COUNT(ff.feedback_id) AS total_interactions
FROM {{var("target_schema")}}.fact_feedback ff
LEFT JOIN {{var("target_schema")}}.dim_songs ds
ON ff.song_id = ds.song_id
LEFT JOIN {{var("target_schema")}}.dim_artists da
ON ds.artist_id = da.artist_id
GROUP BY 1,2,3
