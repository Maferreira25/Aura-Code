def transfer(accounts, source, destination, amount, fail_after_debit=False):
    if accounts[source] < amount:
        raise ValueError("insufficient funds")
    accounts[source] -= amount
    if fail_after_debit:
        raise RuntimeError("injected failure")
    accounts[destination] += amount
