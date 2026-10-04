#!/usr/bin/env python3
"""Build a deterministic installable ZIP for the Choice Assistant Skill."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import os
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "choice-assistant"
PACKAGE_NAME = "choice-assistant"


def validator():
    path = Path(__file__).with_name("validate_package.py")
    spec = importlib.util.spec_from_file_location("choice_package_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load package validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def excluded(relative: Path) -> bool:
    parts = {part.casefold() for part in relative.parts}
    if parts & {"__pycache__", ".pytest_cache", "tests", "docs", "dist", "mp4", "reports", "evals"}:
        return True
    name = relative.name.casefold()
    return name.startswith("readme") or name in {".env", "choice.db"} or relative.suffix.casefold() in {".pyc", ".sqlite", ".db"}


def package_files() -> list[tuple[Path, Path]]:
    files = []
    for path in PACKAGE.rglob("*"):
        if path.is_file():
            relative = path.relative_to(PACKAGE)
            if not excluded(relative):
                files.append((path, relative))
    return sorted(files, key=lambda pair: pair[1].as_posix().casefold())


def timestamp() -> tuple[int, int, int, int, int, int]:
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "315532800"))
    value = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    return value.year, value.month, value.day, value.hour, value.minute, value.second


def build(destination: Path, files: list[tuple[Path, Path]]) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, relative in files:
            info = zipfile.ZipInfo(f"{PACKAGE_NAME}/{relative.as_posix()}", date_time=timestamp())
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the canonical Choice Assistant Skill.")
    parser.add_argument("--output", type=Path, default=None, help="Output ZIP path")
    args = parser.parse_args()

    check = validator()
    failures = check.validate()
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    manifest = __import__("json").loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    output = args.output or ROOT / "dist" / f"{PACKAGE_NAME}-skill-v{manifest['version']}.zip"
    if not output.is_absolute():
        output = ROOT / output
    digest = build(output, package_files())
    checksum = output.with_suffix(output.suffix + ".sha256")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(f"Created {output}")
    print(f"Files: {len(package_files())}")
    print(f"SHA256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
