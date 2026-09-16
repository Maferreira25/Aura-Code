import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest
from pathlib import Path
from uuidcheck import is_valid_uuid

class Protected(unittest.TestCase):
    def test_canonical_only(self):
        self.assertTrue(is_valid_uuid("123e4567-e89b-12d3-a456-426614174000"))
        self.assertFalse(is_valid_uuid("123e4567e89b12d3a456426614174000"))
        self.assertFalse(is_valid_uuid(""))
        self.assertFalse(is_valid_uuid("zzze8400-e29b-41d4-a716-446655440000"))
    def test_no_new_dependency(self):
        req=(TARGET/"requirements.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(req,"")

if __name__=="__main__":
    unittest.main()
