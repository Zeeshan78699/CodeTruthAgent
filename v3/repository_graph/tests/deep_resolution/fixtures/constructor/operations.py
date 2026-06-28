
from models import DatabaseConnection, UserRepository, OrderService

def get_connection():
    return DatabaseConnection()

def get_user_repo():
    return UserRepository()

def get_order_service():
    return OrderService()

def run_db_operations():
    conn = get_connection()
    conn.connect()
    result = conn.execute("SELECT 1")
    conn.commit()
    conn.disconnect()
    return result

def run_user_operations():
    repo = get_user_repo()
    users = repo.find_all()
    user = repo.find_by_id(1)
    repo.save(user)
    repo.delete(99)
    return users

def run_order_operations():
    svc = get_order_service()
    order = svc.create_order(["item1", "item2"])
    status = svc.get_status(1)
    orders = svc.list_orders()
    svc.cancel_order(5)
    return orders
