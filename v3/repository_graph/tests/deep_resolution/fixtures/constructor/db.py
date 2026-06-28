
class DatabaseConnection:
    def connect(self): pass
    def disconnect(self): pass
    def execute(self, query: str): return []
    def commit(self): pass
    def rollback(self): pass
    def is_connected(self) -> bool: return True

class ConnectionPool:
    def acquire(self) -> DatabaseConnection: return DatabaseConnection()
    def release(self, conn): pass
    def size(self) -> int: return 10
