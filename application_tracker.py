import json
import os
from typing import Any, Dict, List


def append_application(project_dir: str, entry: Dict[str, Any]) -> str:
    tracker_path = os.path.join(project_dir, "outputs", "applications_tracker.json")
    os.makedirs(os.path.dirname(tracker_path), exist_ok=True)

    existing: List[Dict[str, Any]] = []
    if os.path.exists(tracker_path):
        with open(tracker_path, encoding="utf-8") as handle:
            try:
                existing = json.load(handle)
            except json.JSONDecodeError:
                existing = []

    if not isinstance(existing, list):
        existing = []

    existing.append(entry)
    with open(tracker_path, "w", encoding="utf-8") as handle:
        json.dump(existing, handle, indent=2)

    return tracker_path
