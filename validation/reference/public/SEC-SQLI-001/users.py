def search_users(conn, term):
    pattern = f"%{term.lower()}%"
    return list(conn.execute(
        "SELECT id, name FROM users WHERE lower(name) LIKE ? ORDER BY id",
        (pattern,),
    ))
