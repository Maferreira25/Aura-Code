import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from cache import Cache

class Protected(unittest.TestCase):
    def test_bounded(self):
        c=Cache(50)
        for i in range(5000):
            c.set(str(i),i)
        self.assertLessEqual(len(c),50)
    def test_lru_read_updates_recency(self):
        c=Cache(2)
        c.set("a",1); c.set("b",2)
        self.assertEqual(c.get("a"),1)
        c.set("c",3)
        self.assertEqual(c.get("a"),1)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("c"),3)

if __name__=="__main__":
    unittest.main()
