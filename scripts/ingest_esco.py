#!/usr/bin/env python3
"""Convert the official ESCO skills export into a SkillBridge merge CSV.

ESCO (European Skills, Competences, Qualifications and Occupations) is the EU's
free, multilingual reference taxonomy of ~13,900 skills. It is the real,
authoritative vocabulary this project normalises against in production.

Usage
-----
1. Download the ESCO classification (CSV, your language) from the official
   portal — it is free but requires accepting the licence:
       https://esco.ec.europa.eu/en/use-esco/download
   You will get files such as ``skills_en.csv``.

2. Run this script to convert it into the merge format the taxonomy store
   understands (id,name,category,aliases):

       python scripts/ingest_esco.py /path/to/skills_en.csv \
           --out data/taxonomy/esco_skills.csv

3. Point the backend at it by setting in backend/.env:
       ESCO_SKILLS_CSV=data/taxonomy/esco_skills.csv

The curated seed taxonomy always takes precedence on ID collisions, so your
hand-tuned aliases are preserved while ESCO fills in long-tail coverage.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.lower()).strip("-")
    return slug[:80] or "skill"


def convert(src: Path, out: Path) -> int:
    if not src.exists():
        print(f"ERROR: input file not found: {src}", file=sys.stderr)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    written = 0

    with src.open(encoding="utf-8-sig", newline="") as fh_in, out.open(
        "w", encoding="utf-8", newline=""
    ) as fh_out:
        reader = csv.DictReader(fh_in)
        writer = csv.writer(fh_out)
        writer.writerow(["id", "name", "category", "aliases"])

        # ESCO column names (English export).
        for row in reader:
            name = (row.get("preferredLabel") or "").strip()
            if not name:
                continue
            uri = (row.get("conceptUri") or "").strip()
            # Prefer a stable ESCO URI tail as ID; fall back to a slug.
            esco_id = uri.rsplit("/", 1)[-1] if uri else slugify(name)
            esco_id = f"esco:{esco_id}" if uri else f"esco:{slugify(name)}"
            if esco_id in seen:
                continue
            seen.add(esco_id)

            raw_alts = row.get("altLabels") or ""
            aliases = [a.strip() for a in re.split(r"[\n|]", raw_alts) if a.strip()]
            category = (row.get("skillType") or row.get("reuseLevel") or "ESCO").strip()

            writer.writerow([esco_id, name, category, "|".join(aliases)])
            written += 1

    print(f"Wrote {written} skills -> {out}")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to ESCO skills_en.csv")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/taxonomy/esco_skills.csv"),
        help="Output merge CSV path",
    )
    args = parser.parse_args()
    count = convert(args.input, args.out)
    return 0 if count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
