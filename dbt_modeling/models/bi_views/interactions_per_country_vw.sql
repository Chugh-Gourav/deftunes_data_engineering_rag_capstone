SELECT
EXTRACT(MONTH FROM ff.timestamp) AS interaction_month,
EXTRACT(YEAR FROM ff.timestamp) AS interaction_year,
du.country_code,
ff.action,
COUNT(ff.feedback_id) AS total_interactions
FROM {{var("target_schema")}}.fact_feedback ff
LEFT JOIN {{var("target_schema")}}.dim_users du
ON ff.user_id = du.user_id
GROUP BY 1,2,3,4
