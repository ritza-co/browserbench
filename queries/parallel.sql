-- Benchmark 5: Parallel session handling
-- Query over batch-level records (one row per batch run)

-- Batch summary: parallel wall-clock, sequential equivalent, overhead ratio, success rate
SELECT
    provider,
    sequential_mode,
    COUNT(*) AS runs,
    ROUND(AVG(sessions_succeeded), 1) AS avg_succeeded,
    concurrency AS max_sessions,
    ROUND(AVG(total_parallel_ms)) AS avg_parallel_ms,
    ROUND(MEDIAN(total_parallel_ms)) AS p50_parallel_ms,
    ROUND(AVG(sequential_equivalent_ms)) AS avg_seq_equiv_ms,
    ROUND(AVG(overhead_ratio), 4) AS avg_overhead_ratio,
    SUM(CASE WHEN success THEN 0 ELSE 1 END) AS failed_batches
FROM read_ndjson_auto('results/parallel-*.jsonl')
GROUP BY provider, sequential_mode, concurrency
ORDER BY avg_parallel_ms ASC;
