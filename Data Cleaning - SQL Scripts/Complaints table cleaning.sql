
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.complaints_clean` AS

WITH cleaned AS (
    SELECT
        TRIM(complaint_id) AS complaint_id,
        UPPER(TRIM(customer_id)) AS customer_id,
        SAFE_CAST(complaint_date AS DATE) AS complaint_date,
        TRIM(complaint_category) AS complaint_category,
        TRIM(complaint_status) AS complaint_status,
        SAFE_CAST(resolution_time_hours AS FLOAT64)
            AS resolution_time_hours
    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.complaints`
),

valid_records AS (
    SELECT c.*
    FROM cleaned c
    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` cu
    ON c.customer_id = cu.customer_id
    WHERE c.complaint_id IS NOT NULL
      AND c.complaint_date IS NOT NULL
      AND c.complaint_status IN ('Resolved', 'In Progress', 'Escalated')
      AND c.resolution_time_hours >= 0
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY complaint_id
            ORDER BY complaint_date
        ) AS row_num
    FROM valid_records
)

SELECT * EXCEPT(row_num)
FROM deduplicated
WHERE row_num = 1;
