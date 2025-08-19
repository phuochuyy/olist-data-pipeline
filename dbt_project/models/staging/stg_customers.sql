{{ config(materialized='view') }}

WITH cleaned_customers AS (
    SELECT 
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        TRIM(UPPER(customer_city)) as customer_city,
        TRIM(UPPER(customer_state)) as customer_state,
        created_at
    FROM {{ source('raw', 'customers') }}
    WHERE customer_id IS NOT NULL
),

deduplicated_customers AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY created_at DESC
        ) as rn
    FROM cleaned_customers
)

SELECT 
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    created_at
FROM deduplicated_customers
WHERE rn = 1
