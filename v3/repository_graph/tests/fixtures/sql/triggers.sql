
-- Triggers
CREATE OR REPLACE TRIGGER trg_order_audit
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW
BEGIN
    IF INSERTING THEN
        DBMS_OUTPUT.PUT_LINE('Order inserted: ' || :NEW.id);
    ELSIF UPDATING THEN
        DBMS_OUTPUT.PUT_LINE('Order updated: ' || :NEW.id);
    ELSIF DELETING THEN
        DBMS_OUTPUT.PUT_LINE('Order deleted: ' || :OLD.id);
    END IF;
END trg_order_audit;

CREATE OR REPLACE TRIGGER trg_check_stock
    BEFORE INSERT ON order_items
    FOR EACH ROW
DECLARE
    v_stock NUMBER;
BEGIN
    SELECT stock INTO v_stock
    FROM products
    WHERE id = :NEW.product_id;

    IF v_stock < :NEW.quantity THEN
        RAISE_APPLICATION_ERROR(-20001, 'Insufficient stock');
    END IF;

    UPDATE products
    SET stock = stock - :NEW.quantity
    WHERE id = :NEW.product_id;
END trg_check_stock;
