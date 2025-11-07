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
    success,
    session_creation_ms,
    session_connect_ms,
    page_goto_ms,
    session_release_ms,
    (session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms) AS total_ms
  FROM pre
  WHERE success = true
),
metric_long AS (
  SELECT provider, 'session_creation_ms' AS metric, session_creation_ms AS value FROM pre_success
  UNION ALL
  SELECT provider, 'session_connect_ms'  AS metric, session_connect_ms  AS value FROM pre_success
  UNION ALL
  SELECT provider, 'page_goto_ms'        AS metric, page_goto_ms        AS value FROM pre_success
  UNION ALL
  SELECT provider, 'session_release_ms'  AS metric, session_release_ms  AS value FROM pre_success
  UNION ALL
  SELECT provider, 'total_ms'            AS metric, total_ms            AS value FROM pre_success
),
success_rate AS (
  SELECT
    provider,
    100.0 * AVG(CASE WHEN success THEN 1 ELSE 0 END)::DOUBLE AS success_rate,
    COUNT(*) AS row_count
  FROM pre
  GROUP BY provider
),
metric_stats_by_provider AS (
  SELECT
    provider,
    metric,
    AVG(value)                 AS avg_ms,
    MEDIAN(value)              AS median_ms,
    quantile_cont(value, 0.95) AS p95_ms,
    quantile_cont(value, 0.99) AS p99_ms,
    STDDEV(value)              AS stddev_ms
  FROM metric_long
  GROUP BY provider, metric
)
SELECT
  ms.provider,
  sr.row_count,
  ROUND(sr.success_rate, 2) AS success_rate,
  ms.metric,
  ROUND(ms.avg_ms,    2) AS avg_ms,
  ROUND(ms.median_ms, 2) AS median_ms,
  ROUND(ms.p95_ms,    2) AS p95_ms,
  ROUND(ms.p99_ms,    2) AS p99_ms,
  ROUND(ms.stddev_ms, 2) AS stddev_ms
FROM metric_stats_by_provider ms
LEFT JOIN success_rate sr USING (provider)
ORDER BY
  provider,
  CASE ms.metric
    WHEN 'session_creation_ms' THEN 1
    WHEN 'session_connect_ms'  THEN 2
    WHEN 'page_goto_ms'        THEN 3
    WHEN 'session_release_ms'  THEN 4
    WHEN 'total_ms'            THEN 5
    ELSE 99
  END;

