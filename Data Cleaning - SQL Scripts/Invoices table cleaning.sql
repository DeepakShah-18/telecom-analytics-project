
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.invoices_clean` AS

WITH cleaned AS (
    SELECT
        TRIM(invoice_id) AS invoice_id,
        UPPER(TRIM(customer_id)) AS customer_id,

        SAFE_CAST(invoice_date AS DATE) AS invoice_date,
        SAFE_CAST(due_date AS DATE) AS due_date,

        SAFE_CAST(billed_amount_inr AS NUMERIC)
            AS billed_amount_inr,

        SAFE_CAST(outstanding_amount_inr AS NUMERIC)
            AS outstanding_amount_inr,

        TRIM(invoice_status) AS invoice_status

    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.invoices`
),

valid_records AS (
    SELECT c.*
    FROM cleaned c
    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.customers_clean` cu
    ON c.customer_id = cu.customer_id
    WHERE c.invoice_id IS NOT NULL
      AND c.invoice_date IS NOT NULL
      AND c.due_date >= c.invoice_date
      AND c.billed_amount_inr > 0
      AND c.outstanding_amount_inr BETWEEN 0 AND c.billed_amount_inr
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY invoice_id
            ORDER BY invoice_date
        ) AS row_num
    FROM valid_records
)

SELECT
    invoice_id,
    customer_id,
    invoice_date,
    due_date,
    billed_amount_inr,
    outstanding_amount_inr,
    CASE
        WHEN outstanding_amount_inr = 0 THEN 'Paid'
        WHEN outstanding_amount_inr = billed_amount_inr THEN 'Unpaid'
        ELSE 'Partially Paid'
    END AS invoice_status
FROM deduplicated
WHERE row_num = 1;
