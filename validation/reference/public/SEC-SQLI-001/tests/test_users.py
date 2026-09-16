import unittest, sqlite3
from users import search_users

def db():
    c=sqlite3.connect(":memory:")
    c.execute("create table users(id integer primary key, name text)")
    c.executemany("insert into users(name) values(?)",[("Alice",),("Bob",),("Alicia",)])
    return c

class Tests(unittest.TestCase):
    def test_literal(self):
        c=db()
        self.assertEqual([r[1] for r in search_users(c,"ali")],["Alice","Alicia"])

if __name__=="__main__":
    unittest.main()
