#!/usr/bin/env python3
"""Post-commit helper: seed changed .md and .json files to the Smart Library API."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MAX_CONTENT_LENGTH = 8000
SKIP_DIRS = {".git", "node_modules", ".chroma_db"}
SUPPORTED_EXTENSIONS = {".md": "Documentation", ".json": "Reference Data"}


def get_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def _parse_lines(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def get_changed_files(repo_root: Path) -> list[str]:
    """Return paths changed in the last commit; fall back to staged files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return _parse_lines(result.stdout)

    # First commit has no HEAD~1 parent.
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _parse_lines(result.stdout)

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return _parse_lines(result.stdout)
    return []


def should_process(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in SKIP_DIRS for part in parts):
        return False
    ext = Path(normalized).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def post_seed(api_url: str, content: str, category: str, language: str = "All") -> None:
    payload = json.dumps(
        {"content": content, "category": category, "language": language}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/seed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed changed documentation and JSON files to the Smart Library API."
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Smart Library API base URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    try:
        repo_root = get_repo_root()
    except subprocess.CalledProcessError:
        print("Warning: not a git repository; skipping seed.", file=sys.stderr)
        return 0

    changed = get_changed_files(repo_root)
    to_seed = [path for path in changed if should_process(path)]

    if not to_seed:
        print("No .md or .json files to seed.")
        return 0

    seeded: list[str] = []
    failed: list[str] = []
    skipped = 0

    for rel_path in to_seed:
        full_path = repo_root / rel_path
        if not full_path.is_file():
            print(f"  skip (missing): {rel_path}")
            skipped += 1
            continue

        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"  skip (read error): {rel_path} — {exc}")
            skipped += 1
            continue

        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH]

        category = SUPPORTED_EXTENSIONS[Path(rel_path).suffix.lower()]
        try:
            post_seed(args.api_url, text, category)
            seeded.append(rel_path)
            print(f"  seeded: {rel_path}")
        except urllib.error.URLError as exc:
            print(
                f"Warning: API unreachable ({args.api_url}): {exc}",
                file=sys.stderr,
            )
            print(
                "Commit was not blocked. Start the API with scripts/run-dev.ps1 or run-dev.sh.",
                file=sys.stderr,
            )
            return 0
        except urllib.error.HTTPError as exc:
            print(f"  failed ({exc.code}): {rel_path}", file=sys.stderr)
            failed.append(rel_path)

    print(
        f"\nSummary: {len(seeded)} seeded, {len(failed)} failed, {skipped} skipped"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())