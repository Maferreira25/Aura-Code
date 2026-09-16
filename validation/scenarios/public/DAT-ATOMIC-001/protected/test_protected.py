import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from ledger import transfer

class Protected(unittest.TestCase):
    def test_failure_rolls_back(self):
        a={"alice":100,"bob":0}
        with self.assertRaises(RuntimeError):
            transfer(a,"alice","bob",25,fail_after_debit=True)
        self.assertEqual(a,{"alice":100,"bob":0})

if __name__=="__main__":
    unittest.main()
