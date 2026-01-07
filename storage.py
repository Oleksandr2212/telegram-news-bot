import json
from pathlib import Path

POSTED_FILE = Path("posted.json")

def load_posted() -> set[str]:
    if not POSTED_FILE.exists():
        return set()
    try:
        data = json.loads(POSTED_FILE.read_text(encoding="utf-8"))
        return set(data)
    except Exception:
        return set()

def save_posted(posted: set[str]) -> None:
    POSTED_FILE.write_text(
        json.dumps(sorted(list(posted)), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
