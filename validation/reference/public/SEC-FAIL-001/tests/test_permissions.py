import unittest
from permissions import may_delete

class Client:
    def __init__(self,v): self.v=v
    def allowed(self,*a): return self.v

class Tests(unittest.TestCase):
    def test_allow(self): self.assertTrue(may_delete("a",Client(True)))
    def test_deny(self): self.assertFalse(may_delete("a",Client(False)))

if __name__=="__main__":
    unittest.main()
