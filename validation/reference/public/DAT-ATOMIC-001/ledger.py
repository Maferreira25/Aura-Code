def transfer(accounts, source, destination, amount, fail_after_debit=False):
    if accounts[source] < amount:
        raise ValueError("insufficient funds")
    before_source = accounts[source]
    before_destination = accounts[destination]
    try:
        accounts[source] -= amount
        if fail_after_debit:
            raise RuntimeError("injected failure")
        accounts[destination] += amount
    except Exception:
        accounts[source] = before_source
        accounts[destination] = before_destination
        raise
