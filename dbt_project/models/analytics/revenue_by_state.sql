-- Delivered revenue per customer state (item price, freight excluded)
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS customers,
    ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
    ROUND((SUM(oi.price) / COUNT(DISTINCT o.order_id))::numeric, 2) AS avg_order_value
FROM {{ ref('stg_customers') }} c
JOIN {{ source('raw', 'orders') }} o ON c.customer_id = o.customer_id
JOIN {{ source('raw', 'order_items') }} oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
