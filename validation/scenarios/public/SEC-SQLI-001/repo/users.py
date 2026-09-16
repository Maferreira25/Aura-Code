def search_users(conn, term):
    sql = f"SELECT id, name FROM users WHERE lower(name) LIKE '%{term.lower()}%' ORDER BY id"
    return list(conn.execute(sql))
