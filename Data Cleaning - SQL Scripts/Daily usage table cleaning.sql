
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.daily_usage_clean` AS

WITH cleaned AS (
    SELECT
        UPPER(TRIM(customer_id)) AS customer_id,

        COALESCE(
            SAFE.PARSE_DATE('%Y-%m-%d', usage_date),
            SAFE.PARSE_DATE('%d/%m/%Y', usage_date)
        ) AS usage_date,

        SAFE_CAST(daily_data_consumption_gb AS FLOAT64)
            AS daily_data_consumption_gb,

        SAFE_CAST(call_minutes AS INT64) AS call_minutes,

        SAFE_CAST(
            SAFE_CAST(sms_count AS FLOAT64) AS INT64
        ) AS sms_count

    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.daily_usage`

    WHERE LOWER(TRIM(customer_id)) != 'customer_id'
),

valid_records AS (
    SELECT *
    FROM cleaned
    WHERE customer_id IS NOT NULL
      AND customer_id != ''
      AND usage_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31'
      AND daily_data_consumption_gb BETWEEN 0 AND 100
      AND call_minutes BETWEEN 0 AND 1440
      AND sms_count >= 0
),

matched_customers AS (
    SELECT v.*
    FROM valid_records v
    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` c
    ON v.customer_id = c.customer_id
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id, usage_date
            ORDER BY customer_id
        ) AS row_num
    FROM matched_customers
)

SELECT * EXCEPT(row_num)
FROM deduplicated
WHERE row_num = 1;
