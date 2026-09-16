import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from documents import get_document

class Protected(unittest.TestCase):
    def test_cross_user_denied(self):
        with self.assertRaises(PermissionError):
            get_document("bob","d1")
    def test_owner_still_works(self):
        self.assertEqual(get_document("bob","d2")["owner"], "bob")

if __name__ == "__main__":
    unittest.main()
