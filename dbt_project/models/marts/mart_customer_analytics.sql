{{ config(materialized='table') }}

WITH customer_orders AS (
    SELECT 
        c.customer_id,
        c.customer_unique_id,
        c.customer_state,
        c.customer_city,
        o.order_id,
        o.order_purchase_timestamp,
        o.order_status,
        oi.price,
        oi.freight_value,
        p.product_category_name
    FROM {{ ref('stg_customers') }} c
    JOIN {{ source('raw', 'orders') }} o ON c.customer_id = o.customer_id
    JOIN {{ source('raw', 'order_items') }} oi ON o.order_id = oi.order_id
    LEFT JOIN {{ source('raw', 'products') }} p ON oi.product_id = p.product_id
    WHERE o.order_status = 'delivered'
),

customer_metrics AS (
    SELECT 
        customer_id,
        customer_unique_id,
        customer_state,
        customer_city,
        COUNT(DISTINCT order_id) as total_orders,
        SUM(price + freight_value) as total_spent,
        AVG(price + freight_value) as avg_order_value,
        MIN(order_purchase_timestamp::date) as first_order_date,
        MAX(order_purchase_timestamp::date) as last_order_date,
        MAX(order_purchase_timestamp::date) - MIN(order_purchase_timestamp::date) as customer_lifetime_days,
        MODE() WITHIN GROUP (ORDER BY product_category_name) as favorite_category
    FROM customer_orders
    GROUP BY customer_id, customer_unique_id, customer_state, customer_city
),

customer_segments AS (
    SELECT *,
        CASE 
            WHEN total_spent >= 1000 AND total_orders >= 5 THEN 'VIP'
            WHEN total_spent >= 500 AND total_orders >= 3 THEN 'Premium'
            WHEN total_spent >= 100 AND total_orders >= 2 THEN 'Regular'
            ELSE 'New'
        END as customer_segment,
        CASE 
            WHEN customer_lifetime_days > 365 THEN 'Long-term'
            WHEN customer_lifetime_days > 90 THEN 'Medium-term'
            ELSE 'Short-term'
        END as customer_tenure
    FROM customer_metrics
)

SELECT 
    customer_id,
    customer_unique_id,
    customer_state,
    customer_city,
    total_orders,
    ROUND(total_spent::numeric, 2) as total_spent,
    ROUND(avg_order_value::numeric, 2) as avg_order_value,
    first_order_date,
    last_order_date,
    customer_lifetime_days,
    favorite_category,
    customer_segment,
    customer_tenure,
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at
FROM customer_segments
