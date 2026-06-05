def insert_user_record(conn, user):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users VALUES (?)', (user,))
    conn.commit()
    return cursor
