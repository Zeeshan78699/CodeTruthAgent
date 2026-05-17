def open_connection():
    config = {
        "host": "test-server",
        "port": 3306,
        "database": "test_db",
        "engine": "mysql"
    }
    return config