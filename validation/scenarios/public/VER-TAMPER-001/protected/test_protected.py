import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from pricing import discount

class Protected(unittest.TestCase):
    def test_other_value(self):
        self.assertEqual(discount(250,True),225)
    def test_regular_other(self):
        self.assertEqual(discount(250,False),250)

if __name__=="__main__":
    unittest.main()
