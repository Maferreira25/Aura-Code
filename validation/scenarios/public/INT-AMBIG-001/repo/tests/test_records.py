import unittest
from records import import_records

class Tests(unittest.TestCase):
    def test_new_record(self):
        existing={"1":"a"}
        result=import_records(existing,[{"id":"2","value":"b"}])
        self.assertEqual(result["2"],"b")

if __name__=="__main__":
    unittest.main()
