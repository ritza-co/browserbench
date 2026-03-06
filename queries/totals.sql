-- Quick total comparison across providers
-- Usage: duckdb -c ".read queries/totals.sql"

WITH data AS (
  SELECT *
  FROM read_json_auto('results/*.jsonl', format='newline_delimited')
),
pre AS (
  SELECT
    provider,
    success,
    try_cast(session_creation_ms AS DOUBLE) AS session_creation_ms,
    try_cast(session_connect_ms  AS DOUBLE) AS session_connect_ms,
    try_cast(page_goto_ms        AS DOUBLE) AS page_goto_ms,
    try_cast(session_release_ms  AS DOUBLE) AS session_release_ms
  FROM data
  WHERE success = true
)
SELECT
  provider,
  COUNT(*) AS runs,
  ROUND(AVG(session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms), 0) AS avg_total_ms,
  ROUND(MEDIAN(session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms), 0) AS median_total_ms,
  ROUND(AVG(session_creation_ms), 0) AS avg_create_ms,
  ROUND(AVG(session_connect_ms), 0)  AS avg_connect_ms,
  ROUND(AVG(page_goto_ms), 0)        AS avg_goto_ms,
  ROUND(AVG(session_release_ms), 0)  AS avg_release_ms
FROM pre
GROUP BY provider
ORDER BY avg_total_ms ASC;
