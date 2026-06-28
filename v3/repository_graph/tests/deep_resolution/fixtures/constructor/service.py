
from db import DatabaseConnection, ConnectionPool
from repository import execute_query, run_transaction

def create_connection() -> DatabaseConnection:
    return DatabaseConnection()

def create_pool() -> ConnectionPool:
    return ConnectionPool()

def run_service():
    conn = create_connection()
    pool = create_pool()

    r1 = execute_query(conn, "SELECT * FROM users")
    r2 = execute_query(conn, "SELECT * FROM orders")

    success = run_transaction(conn, [
        "UPDATE users SET active=1",
        "INSERT INTO logs VALUES (1)",
    ])

    acquired = pool.acquire()
    acquired.connect()
    data = acquired.execute("SELECT count(*) FROM products")
    acquired.commit()
    acquired.disconnect()
    pool.release(acquired)

    conn.disconnect()
    return {"users": r1, "orders": r2, "success": success, "data": data}
