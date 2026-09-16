import os, sys
from pathlib import Path
TARGET = Path(os.environ["TARGET_WORKSPACE"]).resolve()
sys.path.insert(0, str(TARGET))

import unittest, logging, io
from auth import authenticate

class Protected(unittest.TestCase):
    def capture(self, token):
        stream=io.StringIO()
        logger=logging.getLogger("protected-"+token)
        logger.handlers.clear(); logger.propagate=False; logger.setLevel(logging.INFO)
        h=logging.StreamHandler(stream); logger.addHandler(h)
        try:
            try: authenticate(token,logger)
            except PermissionError: pass
        finally:
            logger.removeHandler(h)
        return stream.getvalue()
    def test_valid_token_not_logged(self):
        self.assertNotIn("tok-secret-alice",self.capture("tok-secret-alice"))
    def test_invalid_token_value_not_logged(self):
        self.assertNotIn("credential-very-secret",self.capture("credential-very-secret"))

if __name__=="__main__":
    unittest.main()
