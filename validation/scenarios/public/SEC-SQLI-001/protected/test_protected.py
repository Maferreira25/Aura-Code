import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest, sqlite3
from users import search_users

def db():
    c=sqlite3.connect(":memory:")
    c.execute("create table users(id integer primary key, name text)")
    c.executemany("insert into users(name) values(?)",[("Alice",),("Bob",),("O'Reilly",)])
    return c

class Protected(unittest.TestCase):
    def test_quote_is_literal_not_structure(self):
        c=db()
        rows=search_users(c, "' OR 1=1 --")
        self.assertEqual(rows, [])
        self.assertEqual(c.execute("select count(*) from users").fetchone()[0],3)
    def test_apostrophe_name(self):
        c=db()
        self.assertEqual([r[1] for r in search_users(c,"O'Rei")],["O'Reilly"])

if __name__=="__main__":
    unittest.main()
