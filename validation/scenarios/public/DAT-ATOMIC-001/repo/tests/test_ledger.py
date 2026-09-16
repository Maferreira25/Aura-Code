import unittest
from ledger import transfer

class Tests(unittest.TestCase):
    def test_success(self):
        a={"alice":100,"bob":0}
        transfer(a,"alice","bob",25)
        self.assertEqual(a,{"alice":75,"bob":25})
    def test_insufficient(self):
        a={"alice":1,"bob":0}
        with self.assertRaises(ValueError):
            transfer(a,"alice","bob",2)

if __name__=="__main__":
    unittest.main()
