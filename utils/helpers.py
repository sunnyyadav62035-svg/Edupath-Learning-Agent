import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    """Load a JSON file safely so the app remains usable if data is unavailable."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def title_case_skill(skill_id: str, skills: dict[str, dict]) -> str:
    return skills.get(skill_id, {}).get("name", skill_id.replace("_", " ").title())


def clamp_level(value: int | float) -> int:
    return max(0, min(5, int(value)))


def safe_filename(value: str) -> str:
    return "".join(char for char in value if char.isalnum() or char in ("-", "_")) or "edupath-report"
