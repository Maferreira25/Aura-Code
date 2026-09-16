import unittest
from documents import get_document

class Tests(unittest.TestCase):
    def test_owner_can_read(self):
        self.assertEqual(get_document("alice","d1")["text"], "Alice private")
    def test_missing(self):
        with self.assertRaises(KeyError):
            get_document("alice","missing")

if __name__ == "__main__":
    unittest.main()
