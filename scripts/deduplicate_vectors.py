#!/usr/bin/env python3
"""CLI utility to deduplicate overlapping documents in the Chroma vector store."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from smart_code_lib.config import load_env  # noqa: E402

load_env()

from smart_code_lib.database.vector_store import VectorMemoryStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate overlapping documents in the Chroma vector store."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.95,
        help="Cosine similarity threshold for near-duplicates (default: 0.95)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Preview removals without deleting (default)",
    )
    group.add_argument(
        "--execute",
        dest="dry_run",
        action="store_false",
        help="Actually delete duplicate documents",
    )
    parser.set_defaults(dry_run=True)
    args = parser.parse_args()

    try:
        store = VectorMemoryStore()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    stats = store.deduplicate(
        similarity_threshold=args.threshold,
        dry_run=args.dry_run,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())