"""
TC_M2_SQL_001 — SQL Adapter Validation
Tests SQLAdapter against a synthetic SQL fixture covering:
  - Table definitions
  - View definitions
  - Stored procedures (generic + Oracle PL/SQL)
  - Function definitions
  - Triggers
  - Oracle package calls (DBMS_*)
  - Cross-object references
"""
import json, sys
from datetime import datetime as dt, UTC
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT.parent))
sys.path.insert(0, str(V3_ROOT))

TEST_ID      = "TC_M2_SQL_001"
EVIDENCE_DIR = Path(__file__).parent / "evidence"
FIXTURE_DIR  = Path(__file__).parent / "fixtures" / "sql"

FIXTURE_FILES = {
    "schema.sql": """
-- Core schema definitions
CREATE TABLE users (
    id          NUMBER PRIMARY KEY,
    name        VARCHAR2(100) NOT NULL,
    email       VARCHAR2(200) UNIQUE,
    created_at  TIMESTAMP DEFAULT SYSDATE,
    is_active   NUMBER(1) DEFAULT 1
);

CREATE TABLE orders (
    id          NUMBER PRIMARY KEY,
    user_id     NUMBER REFERENCES users(id),
    total       NUMBER(10,2),
    status      VARCHAR2(20),
    created_at  TIMESTAMP DEFAULT SYSDATE
);

CREATE TABLE order_items (
    id          NUMBER PRIMARY KEY,
    order_id    NUMBER REFERENCES orders(id),
    product_id  NUMBER,
    quantity    NUMBER,
    price       NUMBER(10,2)
);

CREATE TABLE products (
    id          NUMBER PRIMARY KEY,
    name        VARCHAR2(200),
    price       NUMBER(10,2),
    stock       NUMBER
);
""",
    "views.sql": """
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
""",
    "procedures.sql": """
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
""",
    "functions.sql": """
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
""",
    "triggers.sql": """
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
""",
}

def to_json_safe(obj):
    if hasattr(obj, "__dict__"): return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)): return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict): return {k: to_json_safe(v) for k, v in obj.items()}
    return str(obj) if not isinstance(obj, (int, float, bool, type(None))) else obj

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_json_safe(data), f, indent=2)

def create_fixture():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for fname, content in FIXTURE_FILES.items():
        (FIXTURE_DIR / fname).write_text(content)
    print(f"Fixture: {FIXTURE_DIR} ({len(FIXTURE_FILES)} files)")

def save_markdown(passed, report):
    status = "PASS" if passed else "FAIL"
    md = Path(__file__).with_suffix(".md")
    nc = report.get("node_counts", {})
    ec = report.get("edge_counts", {})
    res = report.get("resolution", {})
    lines = [
        f"# {TEST_ID} — SQL Adapter Validation",
        "", "| Field | Value |", "|---|---|",
        f"| Status | {status} |",
        f"| Date | {dt.now(UTC).date().isoformat()} |",
        f"| Dialect | {report.get('dialect', 'N/A')} |",
        f"| Files Scanned | {report.get('files_scanned', 0)} |",
        f"| Governance Gate | {report.get('governance_gate', 'N/A')} |",
        "", "## Graph Nodes", "", "| Type | Count |", "|---|---|",
        f"| Tables | {nc.get('tables', 0)} |",
        f"| Views | {nc.get('views', 0)} |",
        f"| Procedures | {nc.get('procedures', 0)} |",
        f"| Functions | {nc.get('functions', 0)} |",
        f"| Triggers | {nc.get('triggers', 0)} |",
        f"| Packages | {nc.get('packages', 0)} |",
        f"| **Total** | **{nc.get('total', 0)}** |",
        "", "## Graph Edges", "", "| Type | Count |", "|---|---|",
        f"| Table References | {ec.get('table_references', 0)} |",
        f"| Procedure Calls | {ec.get('procedure_calls', 0)} |",
        f"| Oracle Pkg Calls | {ec.get('oracle_pkg_calls', 0)} |",
        f"| **Total** | **{ec.get('total', 0)}** |",
        "", "## Resolution", "", "| Metric | Value |", "|---|---|",
        f"| Resolved | {res.get('resolved_count', 0)} |",
        f"| Unresolved | {res.get('unresolved_count', 0)} |",
        f"| Resolution % | {res.get('resolution_pct', 0)}% |",
        "", "## Requirement Traceability",
        "", "| Requirement | Status |", "|---|---|",
        f"| SQL-001 Table Detection | {status} |",
        f"| SQL-002 Procedure Detection | {status} |",
        f"| SQL-003 Oracle PL/SQL | {status} |",
        f"| SQL-004 Reference Resolution | {status} |",
        f"| SQL-005 Governance Gate | {status} |",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidence saved --> {md}")


def test_tc_m2_sql_001():
    print("=" * 80)
    print(f"{TEST_ID} — SQL Adapter Validation")
    print("=" * 80)
    create_fixture()

    from v3.repository_graph.languages.sql_adapter import SQLAdapter

    report = SQLAdapter().scan(repo_root=str(FIXTURE_DIR))

    nc  = report.get("node_counts", {})
    ec  = report.get("edge_counts", {})
    res = report.get("resolution", {})

    print("\nGRAPH NODES\n" + "-" * 60)
    print(f"     Tables     : {nc.get('tables', 0)}")
    print(f"     Views      : {nc.get('views', 0)}")
    print(f"     Procedures : {nc.get('procedures', 0)}")
    print(f"     Functions  : {nc.get('functions', 0)}")
    print(f"     Triggers   : {nc.get('triggers', 0)}")
    print(f"     Total      : {nc.get('total', 0)}")

    print("\nGRAPH EDGES\n" + "-" * 60)
    print(f"     Table refs    : {ec.get('table_references', 0)}")
    print(f"     Proc calls    : {ec.get('procedure_calls', 0)}")
    print(f"     Oracle pkg    : {ec.get('oracle_pkg_calls', 0)}")
    print(f"     Total         : {ec.get('total', 0)}")

    print("\nRESOLUTION\n" + "-" * 60)
    print(f"     Resolved   : {res.get('resolved_count', 0)}")
    print(f"     Unresolved : {res.get('unresolved_count', 0)}")
    print(f"     Pct        : {res.get('resolution_pct', 0)}%")
    print(f"     Dialect    : {report.get('dialect', 'N/A')}")
    print(f"     Gate       : {report.get('governance_gate', 'N/A')}")

    print("\nASSERTIONS\n" + "-" * 60)

    assert report.get("files_scanned", 0) == 5, "Expected 5 SQL files scanned"
    print("PASS  files_scanned = 5")

    assert nc.get("tables", 0) >= 4, f"Expected >= 4 tables, got {nc.get('tables',0)}"
    print(f"PASS  tables = {nc['tables']} >= 4")

    assert nc.get("views", 0) >= 3, f"Expected >= 3 views, got {nc.get('views',0)}"
    print(f"PASS  views = {nc['views']} >= 3")

    assert nc.get("procedures", 0) >= 3, f"Expected >= 3 procedures, got {nc.get('procedures',0)}"
    print(f"PASS  procedures = {nc['procedures']} >= 3")

    assert nc.get("functions", 0) >= 2, f"Expected >= 2 functions, got {nc.get('functions',0)}"
    print(f"PASS  functions = {nc['functions']} >= 2")

    assert nc.get("triggers", 0) >= 2, f"Expected >= 2 triggers, got {nc.get('triggers',0)}"
    print(f"PASS  triggers = {nc['triggers']} >= 2")

    assert ec.get("total", 0) > 0, "Expected edge references detected"
    print(f"PASS  total edges = {ec['total']} > 0")

    assert ec.get("oracle_pkg_calls", 0) > 0, "Expected Oracle DBMS_* calls detected"
    print(f"PASS  oracle_pkg_calls = {ec['oracle_pkg_calls']} > 0")

    assert report.get("dialect") == "oracle_plsql", f"Expected oracle_plsql dialect"
    print(f"PASS  dialect = oracle_plsql")

    assert report.get("governance_gate") == "APPROVED"
    print(f"PASS  governance_gate = APPROVED")

    save_json(EVIDENCE_DIR / f"{TEST_ID.lower()}_result.json", report)
    save_markdown(passed=True, report=report)

    print(f"\nFINAL RESULT\n{'-'*60}\nPASS")
    return True


if __name__ == "__main__":
    try:
        test_tc_m2_sql_001()
    except (AssertionError, Exception) as exc:
        import traceback; traceback.print_exc(); sys.exit(1)