from pathlib import Path

def read_export(base_dir, filename):
    base = Path(base_dir).resolve()
    raw = Path(filename)
    if raw.is_absolute():
        raise ValueError("absolute paths are not allowed")
    candidate = (base / raw).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError("path escapes base directory") from exc
    return candidate.read_text(encoding="utf-8")
