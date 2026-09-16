import unittest, tempfile
from pathlib import Path
from storage import read_export

class Tests(unittest.TestCase):
    def test_normal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/"a.txt").write_text("ok",encoding="utf-8")
            self.assertEqual(read_export(p,"a.txt"),"ok")

if __name__=="__main__":
    unittest.main()
