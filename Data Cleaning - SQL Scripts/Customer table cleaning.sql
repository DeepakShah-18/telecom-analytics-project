
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` AS

WITH cleaned AS (
    SELECT
        UPPER(TRIM(customer_id)) AS customer_id,
        SAFE_CAST(customer_age AS INT64) AS customer_age,
        COALESCE(NULLIF(TRIM(region), ''), 'Unknown') AS region,
        TRIM(city) AS city,
        TRIM(customer_segment) AS customer_segment,
        TRIM(sales_channel) AS sales_channel,
        SAFE.PARSE_DATE('%Y-%m-%d', signup_date) AS signup_date,
        SAFE_CAST(plan_id AS INT64) AS plan_id,
        TRIM(plan_name) AS plan_name,
        SAFE_CAST(monthly_rental_inr AS NUMERIC) AS monthly_rental_inr,
        SAFE_CAST(data_allowance_gb_per_day AS FLOAT64)
            AS data_allowance_gb_per_day,
        SAFE_CAST(call_allowance_minutes AS INT64)
            AS call_allowance_minutes
    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.customers`
    WHERE LOWER(TRIM(customer_id)) != 'customer_id'
),

valid_records AS (
    SELECT *
    FROM cleaned
    WHERE customer_id IS NOT NULL
      AND customer_id != ''
      AND customer_age BETWEEN 18 AND 100
      AND monthly_rental_inr > 0
      AND signup_date IS NOT NULL
      AND plan_id BETWEEN 101 AND 105
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY customer_id
        ) AS row_num
    FROM valid_records
)

SELECT * EXCEPT(row_num)
FROM deduplicated
WHERE row_num = 1;
