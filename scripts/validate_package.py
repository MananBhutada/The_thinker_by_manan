#!/usr/bin/env python3
"""Validate the canonical installable Choice Assistant Skill package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "choice-assistant"
PRIVATE_PATH = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Object)[\\/]|/(?:Users|home)/)", re.IGNORECASE)
REQUIRED_FILES = (
    "SKILL.md",
    "LICENSE",
    "DISCLAIMER.md",
    "manifest.json",
    "requirements.txt",
    "agents/interface.yaml",
    "backend/main.py",
    "frontend/index.html",
    "scripts/choice_assistant.py",
)
FORBIDDEN_DIRS = {"__pycache__", ".pytest_cache", "tests", "docs", "dist", "mp4", "reports", "evals"}
REQUIRED_TARGETS = {"openai", "claude", "generic", "agent-skills", "vscode"}


def iter_files() -> list[Path]:
    return sorted(
        (
            path
            for path in PACKAGE.rglob("*")
            if path.is_file() and not any(part.casefold() in FORBIDDEN_DIRS for part in path.relative_to(PACKAGE).parts)
        ),
        key=lambda path: path.relative_to(PACKAGE).as_posix().casefold(),
    )


def frontmatter_keys(text: str) -> set[str]:
    if not text.startswith("---\n"):
        return set()
    end = text.find("\n---", 4)
    if end < 0:
        return set()
    return {line.split(":", 1)[0].strip() for line in text[4:end].splitlines() if ":" in line}


def validate() -> list[str]:
    failures: list[str] = []
    if not PACKAGE.is_dir():
        return [f"missing package directory: {PACKAGE}"]

    files = iter_files()
    relative = {path.relative_to(PACKAGE).as_posix() for path in files}
    for required in REQUIRED_FILES:
        if required not in relative:
            failures.append(f"missing required package file: {required}")

    skill_files = [path for path in files if path.name.casefold() == "skill.md"]
    if len(skill_files) != 1 or skill_files[0] != PACKAGE / "SKILL.md":
        failures.append("package must contain exactly one root-level SKILL.md")
    if (ROOT / "SKILL.md").exists():
        failures.append("repository root SKILL.md must be removed after consolidation")

    skill_path = PACKAGE / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text(encoding="utf-8")
        if frontmatter_keys(text) != {"name", "description"}:
            failures.append("SKILL.md frontmatter must contain only name and description")
        if not re.search(r"^name:\s*choice-assistant\s*$", text, re.MULTILINE):
            failures.append("SKILL.md name must be choice-assistant")
        if not re.search(r"^description:\s*\S", text, re.MULTILINE):
            failures.append("SKILL.md description must be non-empty")

    manifest_path = PACKAGE / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid manifest.json: {exc}")
        else:
            if manifest.get("name") != "choice-assistant":
                failures.append("manifest name must match choice-assistant")
            if manifest.get("canonical_path") != "skills/choice-assistant":
                failures.append("manifest canonical_path must be skills/choice-assistant")
            targets = manifest.get("target_platforms")
            if not isinstance(targets, list) or set(targets) != REQUIRED_TARGETS:
                failures.append("manifest target_platforms must declare openai, claude, generic, agent-skills, and vscode")

    interface_path = PACKAGE / "agents" / "interface.yaml"
    if interface_path.is_file():
        interface_text = interface_path.read_text(encoding="utf-8")
        for target in sorted(REQUIRED_TARGETS):
            bullet = rf'^\s*-\s*["\']?{re.escape(target)}["\']?\s*$'
            degradation = rf'^\s*{re.escape(target)}:\s*\S'
            if not re.search(bullet, interface_text, re.MULTILINE):
                failures.append(f"interface adapter_targets missing: {target}")
            if not re.search(degradation, interface_text, re.MULTILINE):
                failures.append(f"interface degradation missing: {target}")

    for path in files:
        rel = path.relative_to(PACKAGE)
        name = path.name.casefold()
        if name.startswith("readme") or name in {".env", "choice.db"} or path.suffix.casefold() in {".pyc", ".sqlite", ".db"}:
            failures.append(f"forbidden install-package file: {rel.as_posix()}")
        if PRIVATE_PATH.search(rel.as_posix()):
            failures.append(f"private path in package member: {rel.as_posix()}")
        if path.suffix.casefold() in {".md", ".json", ".py", ".yaml", ".yml", ".txt"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if PRIVATE_PATH.search(content):
                failures.append(f"private path in package file: {rel.as_posix()}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Valid package: {PACKAGE}")
    print(f"Files: {len(iter_files())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
