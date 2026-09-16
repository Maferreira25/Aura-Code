# Longitudinal Task

This scenario is executed as a sequence. Start from the supplied modular ticket system.

Stage 1: add priority and sorting.
Stage 2: add JSON export.
Stage 3: add audit recording.
Stage 4: add notification through an injected notifier interface.
Stage 5: add filtering by owner and priority.

Preserve these invariants:
- `domain.py` contains domain objects and imports no storage/network modules.
- `service.py` does not import `json`, `sqlite3`, `smtplib`, `requests` or concrete infrastructure modules.
- persistence and external I/O stay behind injected collaborators.
- existing public API remains backward compatible unless a stage explicitly changes it.

Measure architecture fitness after every stage, not only at the end.
