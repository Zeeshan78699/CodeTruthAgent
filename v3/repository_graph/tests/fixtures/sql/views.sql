
-- Business views
CREATE OR REPLACE VIEW active_users AS
    SELECT id, name, email
    FROM users
    WHERE is_active = 1;

CREATE OR REPLACE VIEW order_summary AS
    SELECT
        o.id as order_id,
        u.name as user_name,
        o.total,
        o.status
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE o.status != 'CANCELLED';

CREATE OR REPLACE VIEW product_inventory AS
    SELECT
        p.id,
        p.name,
        p.stock,
        COUNT(oi.id) as pending_orders
    FROM products p
    LEFT JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status = 'PENDING'
    GROUP BY p.id, p.name, p.stock;
