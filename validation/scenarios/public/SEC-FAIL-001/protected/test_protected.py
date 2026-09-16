import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from permissions import may_delete

class Explodes:
    def allowed(self,*a):
        raise TimeoutError("policy unavailable")
class Indeterminate:
    def allowed(self,*a):
        return None

class Protected(unittest.TestCase):
    def test_error_denies(self):
        self.assertFalse(may_delete("a",Explodes()))
    def test_indeterminate_denies(self):
        self.assertFalse(may_delete("a",Indeterminate()))

if __name__=="__main__":
    unittest.main()
