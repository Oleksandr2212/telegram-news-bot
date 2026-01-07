import json
import time
from pathlib import Path

FILE = Path("drafts.json")

def load_drafts() -> dict:
    if not FILE.exists():
        return {}
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_drafts(drafts: dict) -> None:
    FILE.write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")

def new_draft_id() -> str:
    return str(int(time.time()))
