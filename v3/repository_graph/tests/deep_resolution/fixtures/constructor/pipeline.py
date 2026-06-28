
from operations import run_db_operations, run_user_operations, run_order_operations
from models import DatabaseConnection, UserRepository

def execute_pipeline():
    db_results = run_db_operations()
    user_results = run_user_operations()
    order_results = run_order_operations()
    conn = DatabaseConnection()
    conn.connect()
    data = conn.execute("SELECT * FROM orders")
    conn.commit()
    conn.disconnect()
    repo = UserRepository()
    all_users = repo.find_all()
    user = repo.find_by_id(42)
    repo.save({"id": 42, "name": "test"})
    return {"db": db_results, "users": user_results, "all_users": all_users}
