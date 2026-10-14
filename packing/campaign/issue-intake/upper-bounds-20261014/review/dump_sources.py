"""Print `sources.yaml`'s structure: report coordinates, lane mappings and transcribed claims.

Long exact sides are abbreviated. From `packing/`, with the project interpreter::

    python campaign/issue-intake/upper-bounds-20261014/review/dump_sources.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

#: The repository root: this file is packing/campaign/issue-intake/<directory>/review/.
REPO = Path(__file__).resolve().parents[5]
SOURCES = REPO / "packing/campaign/issue-intake/upper-bounds-20261014/sources.yaml"


def emit(*parts: object) -> None:
    """One line of the program's report on standard output."""
    sys.stdout.write(" ".join(str(part) for part in parts) + "\n")


def main() -> None:
    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    emit("exceptions:", sources.get("exceptions"))
    emit("other_items:", [item["issue"] for item in sources.get("other_items", [])])
    for report in sources["reports"]:
        emit("==", {key: report[key] for key in report if key not in ("claims", "lanes")})
        for mapping in report.get("lanes", []):
            emit("   lane:", mapping)
        for claim in report.get("claims", []):
            short = {
                key: value[:24] + "..."
                if key == "exact" and isinstance(value, str) and len(value) > 60
                else value
                for key, value in claim.items()
            }
            emit("   claim:", short)


if __name__ == "__main__":
    main()
