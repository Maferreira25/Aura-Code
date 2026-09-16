import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest, tempfile
from pathlib import Path
from storage import read_export

class Protected(unittest.TestCase):
    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as parent:
            p=Path(parent); base=p/"exports"; base.mkdir()
            (p/"secret.txt").write_text("secret",encoding="utf-8")
            with self.assertRaises(ValueError):
                read_export(base, "../secret.txt")
    def test_nested_inside_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); (base/"nested").mkdir()
            (base/"nested"/"x.txt").write_text("x",encoding="utf-8")
            self.assertEqual(read_export(base,"nested/x.txt"),"x")

if __name__=="__main__":
    unittest.main()
