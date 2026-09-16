class PaymentService:
    def __init__(self):
        self.charges=[]
        self._by_request={}

    def charge(self, request_id, amount):
        if request_id in self._by_request:
            return self._by_request[request_id]
        record={"request_id":request_id,"amount":amount,"sequence":len(self.charges)+1}
        self.charges.append(record)
        self._by_request[request_id]=record
        return record
