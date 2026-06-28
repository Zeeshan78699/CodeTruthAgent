
class DatabaseConnection:
    def connect(self): pass
    def disconnect(self): pass
    def execute(self, q: str): return []
    def commit(self): pass
    def rollback(self): pass

class UserRepository:
    def find_by_id(self, uid: int): return {}
    def save(self, user: dict): pass
    def delete(self, uid: int): pass
    def find_all(self): return []

class OrderService:
    def create_order(self, items: list): return {}
    def cancel_order(self, oid: int): pass
    def get_status(self, oid: int): return "PENDING"
    def list_orders(self): return []
