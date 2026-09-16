# Task

`transfer(accounts, source, destination, amount, fail_after_debit=False)` must be atomic.
If any exception occurs after the operation starts, account balances must remain exactly as they were before the call.
Preserve validation for insufficient funds.
The `fail_after_debit` flag is a deterministic failure injection hook used by tests.
