import unittest
from pricing import discount

class Tests(unittest.TestCase):
    def test_regular(self):
        self.assertEqual(discount(100,False),100)
    def test_premium(self):
        self.assertEqual(discount(100,True),90)
    def test_zero(self):
        self.assertEqual(discount(0,True),0)

if __name__=="__main__":
    unittest.main()
