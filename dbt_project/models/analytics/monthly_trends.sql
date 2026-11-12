-- Delivered orders and revenue per purchase month
SELECT
    DATE_TRUNC('month', o.order_purchase_timestamp)::date AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS customers,
    ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
    ROUND((SUM(oi.price) / COUNT(DISTINCT o.order_id))::numeric, 2) AS avg_order_value
FROM {{ source('raw', 'orders') }} o
JOIN {{ ref('stg_customers') }} c ON c.customer_id = o.customer_id
JOIN {{ source('raw', 'order_items') }} oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
