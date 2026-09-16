# Task

`search_users(conn, term)` must perform a case-insensitive literal substring search over `name`.
User input must never change the SQL structure.
Preserve the return value as a list of `(id, name)` tuples.
