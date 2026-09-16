# Task

`PaymentService.charge(request_id, amount)` may be retried after a timeout.
The same `request_id` must never create a second charge.
Repeated calls with the same request ID must return the original charge record.
Different request IDs remain independent.
