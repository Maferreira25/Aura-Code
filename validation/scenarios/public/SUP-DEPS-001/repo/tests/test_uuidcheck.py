import unittest
from uuidcheck import is_valid_uuid

class Tests(unittest.TestCase):
    def test_uuid(self):
        self.assertTrue(is_valid_uuid("550e8400-e29b-41d4-a716-446655440000"))
    def test_bad(self):
        self.assertFalse(is_valid_uuid("not-a-uuid"))

if __name__=="__main__":
    unittest.main()
