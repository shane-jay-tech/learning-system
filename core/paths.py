"""Learning path system — loads path definitions and tracks milestone progress."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

_PATHS_DIR = str(Path(__file__).resolve().parent.parent / "content" / "paths")


@dataclass
class Milestone:
    id: str
    title: str
    description: str
    topics: List[str]  # e.g. ["python/01_hello_and_vars", "python/02_conditionals"]
    estimated_hours: float
    graduation_project: Optional[str] = None
    prereqs: List[str] = field(default_factory=list)


@dataclass
class LearningPath:
    id: str
    title: str
    subtitle: str
    icon: str
    estimated_hours: float
    milestones: List[Milestone]


_path_cache: dict = {}


def load_path(path_id: str) -> Optional[LearningPath]:
    if path_id in _path_cache:
        return _path_cache[path_id]

    filepath = os.path.join(_PATHS_DIR, f"{path_id}.yaml")
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    milestones = []
    for i, m in enumerate(data.get("milestones", []), 1):
        milestones.append(Milestone(
            id=m.get("id", f"m{i}"),
            title=m["title"],
            description=m.get("description", ""),
            topics=m.get("topics", []),
            estimated_hours=m.get("estimated_hours", 2),
            graduation_project=m.get("graduation_project"),
            prereqs=m.get("prereqs", []),
        ))

    path = LearningPath(
        id=path_id,
        title=data["title"],
        subtitle=data.get("subtitle", ""),
        icon=data.get("icon", ""),
        estimated_hours=data.get("estimated_hours", 0),
        milestones=milestones,
    )
    _path_cache[path_id] = path
    return path


def load_all_paths() -> List[LearningPath]:
    paths = []
    if not os.path.isdir(_PATHS_DIR):
        return paths
    for fname in sorted(os.listdir(_PATHS_DIR)):
        if fname.endswith(".yaml"):
            pid = fname[:-5]
            p = load_path(pid)
            if p:
                paths.append(p)
    return paths


def get_milestone_topics_flat(milestone: Milestone) -> List[tuple]:
    """Return list of (lang, topic_slug) tuples for a milestone's topics."""
    results = []
    for t in milestone.topics:
        parts = t.split("/", 1)
        if len(parts) == 2:
            results.append((parts[0], parts[1]))
    return results
