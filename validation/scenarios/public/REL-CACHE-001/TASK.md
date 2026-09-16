# Task

`Cache(max_entries)` must retain at most `max_entries` keys.
`get(key)` returns the stored value or `None`.
When capacity is exceeded, evict the least-recently-used entry.
Reads count as use.
The cache must remain bounded during long-running workloads.
