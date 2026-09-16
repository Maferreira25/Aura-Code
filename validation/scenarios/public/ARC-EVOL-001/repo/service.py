class TicketService:
    def __init__(self, repository):
        self.repository=repository
    def create(self, ticket):
        self.repository.save(ticket)
        return ticket
    def list(self):
        return self.repository.all()
