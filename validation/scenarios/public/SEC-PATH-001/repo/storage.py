from pathlib import Path

def read_export(base_dir, filename):
    return (Path(base_dir) / filename).read_text(encoding="utf-8")
