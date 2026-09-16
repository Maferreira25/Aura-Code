import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from payments import PaymentService

class Protected(unittest.TestCase):
    def test_duplicate_request_is_idempotent(self):
        s=PaymentService()
        a=s.charge("same",25)
        b=s.charge("same",25)
        self.assertEqual(a,b)
        self.assertEqual(len(s.charges),1)
    def test_distinct_requests_charge(self):
        s=PaymentService()
        s.charge("a",1); s.charge("b",1)
        self.assertEqual(len(s.charges),2)

if __name__=="__main__":
    unittest.main()
