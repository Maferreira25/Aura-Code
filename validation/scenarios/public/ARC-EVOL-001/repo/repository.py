class InMemoryTicketRepository:
    def __init__(self):
        self.items={}
    def save(self,ticket):
        self.items[ticket.id]=ticket
    def all(self):
        return list(self.items.values())
