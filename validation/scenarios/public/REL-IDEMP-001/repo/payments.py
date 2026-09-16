class PaymentService:
    def __init__(self):
        self.charges=[]

    def charge(self, request_id, amount):
        record={"request_id":request_id,"amount":amount,"sequence":len(self.charges)+1}
        self.charges.append(record)
        return record
