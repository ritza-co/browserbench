-- Benchmark 2: Idle workflow results
-- Usage: duckdb -c ".read queries/idle-workflow.sql"

WITH data AS (
  SELECT *
  FROM read_json_auto('results/idle-*.jsonl', format='newline_delimited')
)
SELECT
  provider,
  success,
  session_survived,
  ROUND(try_cast(step1_ms          AS DOUBLE), 0) AS step1_ms,
  ROUND(try_cast(idle_ms           AS DOUBLE) / 1000.0, 1) AS idle_actual_s,
  ROUND(try_cast(reconnect_ms      AS DOUBLE), 0) AS reconnect_ms,
  ROUND(try_cast(step2_ms          AS DOUBLE), 0) AS step2_ms,
  ROUND(try_cast(session_release_ms AS DOUBLE), 0) AS release_ms,
  ROUND(try_cast(total_ms          AS DOUBLE) / 1000.0, 1) AS total_s,
  step2_title,
  error_stage,
  error_message
FROM data
ORDER BY provider;
