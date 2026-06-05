class UserRecord:
    def __init__(self, name):
        self.name = name

def create_user(name):
    user = UserRecord(name)
    return user
