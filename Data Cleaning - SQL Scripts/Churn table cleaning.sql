
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.churn_clean` AS

WITH cleaned AS (
    SELECT
        UPPER(TRIM(customer_id)) AS customer_id,
        TRIM(churn_status) AS churn_status,
        SAFE_CAST(disconnection_date AS DATE) AS disconnection_date,
        TRIM(churn_reason) AS churn_reason,
        SAFE_CAST(churn_risk_score AS FLOAT64) AS churn_risk_score

    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.Churn`
),

valid_records AS (
    SELECT c.*
    FROM cleaned c
    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` cu
    ON c.customer_id = cu.customer_id

    WHERE c.churn_status IN ('Active', 'Churned')
      AND c.churn_risk_score BETWEEN 0 AND 1
      AND (
          (c.churn_status = 'Active'
           AND c.disconnection_date IS NULL)
          OR
          (c.churn_status = 'Churned'
           AND c.disconnection_date IS NOT NULL)
      )
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
