import unittest
from domain import Ticket
from repository import InMemoryTicketRepository
from service import TicketService

class Tests(unittest.TestCase):
    def test_create(self):
        r=InMemoryTicketRepository(); s=TicketService(r)
        t=Ticket("1","x","alice")
        self.assertIs(s.create(t),t)
        self.assertEqual(s.list(),[t])

if __name__=="__main__":
    unittest.main()
