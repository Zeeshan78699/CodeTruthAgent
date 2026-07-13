
-- Stored procedures
CREATE OR REPLACE PROCEDURE create_order(
    p_user_id   IN NUMBER,
    p_total     IN NUMBER,
    p_status    OUT VARCHAR2
) AS
    v_order_id NUMBER;
BEGIN
    INSERT INTO orders (user_id, total, status)
    VALUES (p_user_id, p_total, 'PENDING');

    SELECT MAX(id) INTO v_order_id FROM orders;

    DBMS_OUTPUT.PUT_LINE('Order created: ' || v_order_id);
    DBMS_STATS.GATHER_TABLE_STATS(NULL, 'ORDERS');

    p_status := 'SUCCESS';
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        p_status := 'ERROR';
        DBMS_OUTPUT.PUT_LINE(SQLERRM);
END create_order;

CREATE OR REPLACE PROCEDURE update_user_status(
    p_user_id   IN NUMBER,
    p_is_active IN NUMBER
) AS
BEGIN
    UPDATE users
    SET is_active = p_is_active
    WHERE id = p_user_id;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('User updated: ' || p_user_id);
END update_user_status;

CREATE OR REPLACE PROCEDURE process_orders AS
    CURSOR c_orders IS
        SELECT id, user_id, total
        FROM orders
        WHERE status = 'PENDING';
BEGIN
    FOR rec IN c_orders LOOP
        UPDATE order_items
        SET quantity = quantity
        WHERE order_id = rec.id;

        EXECUTE create_order(rec.user_id, rec.total, 'OUT_STATUS');
    END LOOP;
    COMMIT;
END process_orders;
