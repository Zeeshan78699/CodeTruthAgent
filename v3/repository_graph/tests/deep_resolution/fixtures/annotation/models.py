
class DatabaseConnection:
    def connect(self): pass
    def disconnect(self): pass
    def execute(self, query: str): return []
    def commit(self): pass
    def rollback(self): pass

class UserRepository:
    def find_by_id(self, uid: int): return {}
    def save(self, user: dict): pass
    def find_all(self): return []
    def delete(self, uid: int): pass

class EmailService:
    def send(self, to: str, body: str): pass
    def validate(self, email: str): return True
    def queue(self, message: dict): pass
