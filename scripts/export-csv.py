#!/usr/bin/env python3
"""Export sources to CSV format for spreadsheets."""

import csv
import os
import sys
from pathlib import Path

from frontmatter import parse_frontmatter


def main():
    sources_dir = sys.argv[1] if len(sys.argv) > 1 else "sources"
    output_file = os.path.join(os.path.dirname(sources_dir), "sources.csv")

    sources_path = Path(sources_dir)
    if not sources_path.exists():
        print(f"No sources directory: {sources_dir}", file=sys.stderr)
        sys.exit(1)

    rows = []
    for md_file in sorted(sources_path.glob("source-*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(content)
        if not fm.get("title"):
            continue

        authors = fm.get("authors", [])
        if isinstance(authors, list):
            authors = "; ".join(authors)

        rows.append({
            "title": fm.get("title", ""),
            "authors": authors,
            "year": fm.get("year", ""),
            "journal": fm.get("journal", ""),
            "doi": fm.get("doi", ""),
            "pdf_url": fm.get("pdf_url", ""),
            "type": fm.get("type", ""),
            "relevance": fm.get("relevance", ""),
        })

    if not rows:
        print("No sources found", file=sys.stderr)
        sys.exit(1)

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} sources to {output_file}")


if __name__ == "__main__":
    main()
