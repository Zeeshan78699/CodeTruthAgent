
from db import DatabaseConnection, ConnectionPool

def execute_query(conn: DatabaseConnection, query: str) -> list:
    if not conn.is_connected():
        conn.connect()
    result = conn.execute(query)
    conn.commit()
    return result

def run_transaction(conn: DatabaseConnection, queries: list) -> bool:
    conn.connect()
    try:
        for q in queries:
            conn.execute(q)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.disconnect()

def pool_operations(pool: ConnectionPool) -> list:
    conn = pool.acquire()
    results = execute_query(conn, "SELECT 1")
    pool.release(conn)
    size = pool.size()
    return results
