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
),
pre_success AS (
  SELECT
    provider,
    session_creation_ms,
    session_connect_ms,
    page_goto_ms,
    session_release_ms,
    (session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms) AS total_ms
  FROM pre
  WHERE success = true
)
SELECT
  provider,
  ROUND(AVG(total_ms), 2) AS avg_total_ms
FROM pre_success
GROUP BY provider
ORDER BY provider DESC;
