def connect_database():
    config = {
        "host": "prod-server",
        "port": 5432,
        "database": "main_db",
        "engine": "postgresql"
    }
    return config