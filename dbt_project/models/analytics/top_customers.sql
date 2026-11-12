-- The 500 customers with the highest spend (price + freight, delivered orders)
SELECT
    RANK() OVER (ORDER BY total_spent DESC) AS revenue_rank,
    customer_unique_id,
    customer_state,
    total_orders,
    total_spent AS total_revenue,
    avg_order_value,
    customer_segment,
    favorite_category
FROM {{ ref('mart_customer_analytics') }}
ORDER BY total_spent DESC
LIMIT 500
