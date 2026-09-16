import unittest, logging
from auth import authenticate

class Tests(unittest.TestCase):
    def test_valid(self):
        logger=logging.getLogger("test-valid")
        self.assertEqual(authenticate("tok-secret-alice",logger),"alice")
    def test_invalid(self):
        logger=logging.getLogger("test-invalid")
        with self.assertRaises(PermissionError):
            authenticate("bad",logger)

if __name__=="__main__":
    unittest.main()
