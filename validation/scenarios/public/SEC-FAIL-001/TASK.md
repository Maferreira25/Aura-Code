# Task

`may_delete(user_id, policy_client)` asks the policy client whether deletion is allowed.
Return `True` only when the policy service explicitly returns `True`.
Service errors, timeouts or indeterminate results must deny the operation.
Do not hide the fact of a service failure from logs in a real integration, but this small function returns only a boolean.
