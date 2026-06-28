class DatabaseConnection:
    def connect(self): pass
    def disconnect(self): pass
    def execute(self, q: str): pass
    def fetch_all(self): return []
    def commit(self): pass

class UserRepository:
    def find_by_id(self, uid: int): pass
    def save(self, u): pass

class OrderService:
    def create_order(self, items: list): pass
    def get_status(self, oid: int): return 'PENDING'

def run():
    db = DatabaseConnection()
    db.connect()
    db.execute('SELECT 1')
    r = db.fetch_all()
    db.commit()
    db.disconnect()
    repo = UserRepository()
    u = repo.find_by_id(1)
    repo.save(u)
    svc = OrderService()
    svc.create_order(['a'])
    s = svc.get_status(1)
    return r
