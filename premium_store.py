import json
from pathlib import Path

FILE = Path("premium_users.json")

def load_premium() -> set[int]:
    if not FILE.exists():
        return set()
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        return set(int(x) for x in data)
    except Exception:
        return set()

def save_premium(users: set[int]) -> None:
    FILE.write_text(json.dumps(sorted(list(users)), indent=2), encoding="utf-8")
