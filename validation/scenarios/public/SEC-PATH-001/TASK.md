# Task

`read_export(base_dir, filename)` must read files located inside `base_dir`.
Reject absolute paths and any path that escapes `base_dir`, including traversal such as `../`.
Raise `ValueError` for a rejected path.
Keep normal nested files inside the base directory working.
