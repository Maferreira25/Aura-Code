import unittest
from payments import PaymentService

class Tests(unittest.TestCase):
    def test_single(self):
        s=PaymentService()
        r=s.charge("r1",10)
        self.assertEqual(r["amount"],10)
        self.assertEqual(len(s.charges),1)

if __name__=="__main__":
    unittest.main()
