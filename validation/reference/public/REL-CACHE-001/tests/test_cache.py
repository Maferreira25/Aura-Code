import unittest
from cache import Cache

class Tests(unittest.TestCase):
    def test_get_set(self):
        c=Cache(2); c.set("a",1)
        self.assertEqual(c.get("a"),1)
        self.assertIsNone(c.get("x"))

if __name__=="__main__":
    unittest.main()
