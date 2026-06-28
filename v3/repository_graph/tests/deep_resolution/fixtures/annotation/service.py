
from models import DatabaseConnection, UserRepository, EmailService

def process_users(
    conn: DatabaseConnection,
    repo: UserRepository,
    email: EmailService,
) -> list:
    conn.connect()
    users = repo.find_all()
    for user in users:
        email.send(user["email"], "Hello")
        email.validate(user["email"])
    conn.commit()
    conn.disconnect()
    return users

def save_user(
    conn: DatabaseConnection,
    repo: UserRepository,
    user: dict,
) -> bool:
    conn.connect()
    repo.save(user)
    conn.commit()
    conn.disconnect()
    return True

def delete_user(
    conn: DatabaseConnection,
    repo: UserRepository,
    uid: int,
) -> bool:
    try:
        conn.connect()
        repo.delete(uid)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.disconnect()
