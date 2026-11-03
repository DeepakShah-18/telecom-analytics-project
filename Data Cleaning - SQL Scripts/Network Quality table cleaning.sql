
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.network_quality_clean` AS

WITH cleaned AS (
    SELECT
        UPPER(TRIM(customer_id)) AS customer_id,
        SAFE_CAST(usage_date AS DATE) AS usage_date,

        SAFE_CAST(network_availability_pct AS FLOAT64)
            AS network_availability_pct,

        SAFE_CAST(average_latency_ms AS FLOAT64)
            AS average_latency_ms,

        SAFE_CAST(average_download_speed_mbps AS FLOAT64)
            AS average_download_speed_mbps,

        SAFE_CAST(dropped_calls AS INT64) AS dropped_calls,

        SAFE_CAST(network_quality_score AS FLOAT64)
            AS network_quality_score

    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.network_quality`
),

valid_records AS (
    SELECT n.*
    FROM cleaned n
    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` c
    ON n.customer_id = c.customer_id

    WHERE n.customer_id IS NOT NULL
      AND n.usage_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31'
      AND n.network_availability_pct BETWEEN 0 AND 100
      AND n.average_latency_ms >= 0
      AND n.average_download_speed_mbps >= 0
      AND n.dropped_calls >= 0
      AND n.network_quality_score BETWEEN 0 AND 100
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id, usage_date
            ORDER BY customer_id
        ) AS row_num
    FROM valid_records
)

SELECT * EXCEPT(row_num)
FROM deduplicated
WHERE row_num = 1;
