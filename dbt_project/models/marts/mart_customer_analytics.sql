{{ config(materialized='table') }}

-- One row per real customer. In Olist a new customer_id is issued for every order;
-- customer_unique_id is the person, so repeat purchases are only visible at that grain.

WITH delivered_items AS (
    SELECT
        c.customer_unique_id,
        c.customer_state,
        c.customer_city,
        o.order_id,
        o.order_purchase_timestamp,
        oi.price,
        oi.freight_value,
        COALESCE(t.product_category_name_english, p.product_category_name) AS product_category
    FROM {{ ref('stg_customers') }} c
    JOIN {{ source('raw', 'orders') }} o ON c.customer_id = o.customer_id
    JOIN {{ source('raw', 'order_items') }} oi ON o.order_id = oi.order_id
    LEFT JOIN {{ source('raw', 'products') }} p ON oi.product_id = p.product_id
    LEFT JOIN {{ source('raw', 'product_category_translation') }} t
        ON p.product_category_name = t.product_category_name
    WHERE o.order_status = 'delivered'
),

latest_location AS (
    SELECT DISTINCT ON (customer_unique_id)
        customer_unique_id,
        customer_state,
        customer_city
    FROM delivered_items
    ORDER BY customer_unique_id, order_purchase_timestamp DESC
),

customer_metrics AS (
    SELECT
        customer_unique_id,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(*) AS total_items,
        SUM(price + freight_value) AS total_spent,
        SUM(price + freight_value) / COUNT(DISTINCT order_id) AS avg_order_value,
        MIN(order_purchase_timestamp::date) AS first_order_date,
        MAX(order_purchase_timestamp::date) AS last_order_date,
        MODE() WITHIN GROUP (ORDER BY product_category) AS favorite_category
    FROM delivered_items
    GROUP BY customer_unique_id
),

customer_segments AS (
    SELECT
        m.*,
        l.customer_state,
        l.customer_city,
        m.last_order_date - m.first_order_date AS customer_lifetime_days,
        CASE
            WHEN m.total_spent >= 1000 AND m.total_orders >= 5 THEN 'VIP'
            WHEN m.total_spent >= 500 AND m.total_orders >= 3 THEN 'Premium'
            WHEN m.total_spent >= 100 AND m.total_orders >= 2 THEN 'Regular'
            ELSE 'New'
        END AS customer_segment
    FROM customer_metrics m
    JOIN latest_location l USING (customer_unique_id)
)

SELECT
    customer_unique_id,
    customer_state,
    customer_city,
    total_orders,
    total_items,
    ROUND(total_spent::numeric, 2) AS total_spent,
    ROUND(avg_order_value::numeric, 2) AS avg_order_value,
    first_order_date,
    last_order_date,
    customer_lifetime_days,
    favorite_category,
    customer_segment,
    CASE
        WHEN customer_lifetime_days > 365 THEN 'Long-term'
        WHEN customer_lifetime_days > 90 THEN 'Medium-term'
        ELSE 'Short-term'
    END AS customer_tenure,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM customer_segments
