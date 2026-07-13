
-- Functions
CREATE OR REPLACE FUNCTION get_user_total_orders(
    p_user_id IN NUMBER
) RETURN NUMBER AS
    v_total NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM orders
    WHERE user_id = p_user_id;

    RETURN v_total;
END get_user_total_orders;

CREATE OR REPLACE FUNCTION calculate_discount(
    p_order_id IN NUMBER,
    p_rate     IN NUMBER DEFAULT 0.1
) RETURN NUMBER AS
    v_total   NUMBER;
    v_discount NUMBER;
BEGIN
    SELECT total INTO v_total
    FROM orders
    WHERE id = p_order_id;

    v_discount := v_total * p_rate;
    RETURN v_discount;
END calculate_discount;
