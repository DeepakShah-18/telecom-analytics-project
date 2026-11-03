
CREATE OR REPLACE TABLE
`weighty-actor-513623-m6.Silver_Layer_Clean.payments_clean` AS

WITH cleaned AS (
    SELECT
        TRIM(payment_id) AS payment_id,
        TRIM(invoice_id) AS invoice_id,
        UPPER(TRIM(customer_id)) AS customer_id,

        SAFE_CAST(payment_date AS DATE) AS payment_date,
        SAFE_CAST(payment_amount_inr AS NUMERIC)
            AS payment_amount_inr,

        TRIM(payment_method) AS payment_method,
        TRIM(payment_status) AS payment_status

    FROM
        `weighty-actor-513623-m6.Bronze_Layer_Raw.payments`
),

valid_records AS (
    SELECT p.*
    FROM cleaned p

    INNER JOIN
        `weighty-actor-513623-m6.Silver_Layer_Clean.invoices_clean` i
    ON p.invoice_id = i.invoice_id
       AND p.customer_id = i.customer_id

    WHERE p.payment_id IS NOT NULL
      AND p.payment_date IS NOT NULL
      AND p.payment_amount_inr >= 0
      AND p.payment_status IN ('Successful', 'Failed', 'Pending')
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY payment_id
            ORDER BY payment_date
        ) AS row_num
    FROM valid_records
)

SELECT * EXCEPT(row_num)
FROM deduplicated
WHERE row_num = 1;
