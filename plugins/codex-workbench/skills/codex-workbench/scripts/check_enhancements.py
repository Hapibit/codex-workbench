#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def skill_roots() -> list[Path]:
    roots: list[Path] = []
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        roots.append(Path(env_home).expanduser() / "skills")
    roots.append(Path.home() / ".codex" / "skills")
    return unique_existing_dirs(roots)


def unique_existing_dirs(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.expanduser()
        key = str(resolved).lower() if os.name == "nt" else str(resolved)
        if key in seen or not resolved.exists():
            continue
        seen.add(key)
        result.append(resolved)
    return result


def load_registry(skill_root: Path) -> dict[str, Any]:
    path = skill_root / "assets" / "enhancements.json"
    return json.loads(path.read_text(encoding="utf-8"))


def installed_skills(roots: list[Path]) -> set[str]:
    found: set[str] = set()
    for root in roots:
        for child in root.iterdir():
            if child.is_dir() and (child / "SKILL.md").exists():
                found.add(child.name)
    return found


def match_categories(registry: dict[str, Any], query: str | None) -> set[str]:
    if not query:
        return set()
    normalized = query.lower()
    matches: set[str] = set()
    for category in registry.get("categories", []):
        haystacks = [category.get("id", ""), category.get("label", "")]
        haystacks.extend(category.get("triggers", []))
        if any(str(item).lower() in normalized for item in haystacks):
            matches.add(category["id"])
    return matches


def build_report(registry: dict[str, Any], installed: set[str], query: str | None) -> dict[str, Any]:
    matched = match_categories(registry, query)
    categories = []
    for category in registry.get("categories", []):
        skills = category.get("skills", [])
        available = [skill for skill in skills if skill in installed]
        missing = [skill for skill in skills if skill not in installed]
        categories.append(
            {
                "id": category["id"],
                "label": category["label"],
                "matchedQuery": category["id"] in matched,
                "available": available,
                "missing": missing,
                "status": "available" if available else "missing",
            }
        )
    return {
        "schema": "codex-workbench-enhancement-check/v1",
        "query": query,
        "skillRoots": [str(path) for path in skill_roots()],
        "categories": categories,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional Codex Workbench enhancement skills.")
    parser.add_argument("--query", default=None, help="Optional task text used to highlight relevant enhancement categories.")
    args = parser.parse_args()

    current_skill_root = Path(__file__).resolve().parents[1]
    registry = load_registry(current_skill_root)
    roots = skill_roots()
    report = build_report(registry, installed_skills(roots), args.query)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
