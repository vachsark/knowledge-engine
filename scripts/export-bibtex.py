#!/usr/bin/env python3
"""Export sources to BibTeX format for LaTeX/Zotero/Overleaf."""

import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in content[3:end].strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                # Parse array
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            fm[key] = val
    return fm


def to_bibtex_key(title, year):
    """Generate a BibTeX key from title and year."""
    words = re.sub(r"[^\w\s]", "", title.lower()).split()
    key = words[0] if words else "unknown"
    return f"{key}{year}"


def source_to_bibtex(fm):
    """Convert a source's frontmatter to a BibTeX entry."""
    title = fm.get("title", "Unknown Title")
    authors = fm.get("authors", [])
    year = fm.get("year", "n.d.")
    journal = fm.get("journal", "")
    doi = fm.get("doi", "")
    url = fm.get("pdf_url", "")
    source_type = fm.get("type", "article")

    if isinstance(authors, str):
        authors = [authors]

    key = to_bibtex_key(title, year)
    author_str = " and ".join(authors) if authors else "Unknown"

    entry_type = "article"
    if source_type in ("book-chapter",):
        entry_type = "incollection"
    elif source_type in ("foundational",) and not journal:
        entry_type = "book"

    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title = {{{title}}},")
    lines.append(f"  author = {{{author_str}}},")
    lines.append(f"  year = {{{year}}},")
    if journal:
        lines.append(f"  journal = {{{journal}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if url:
        lines.append(f"  url = {{{url}}},")
    lines.append("}")

    return "\n".join(lines)


def main():
    sources_dir = sys.argv[1] if len(sys.argv) > 1 else "sources"
    output_file = os.path.join(os.path.dirname(sources_dir), "bibliography.bib")

    sources_path = Path(sources_dir)
    if not sources_path.exists():
        print(f"No sources directory: {sources_dir}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for md_file in sorted(sources_path.glob("source-*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        if fm.get("title"):
            entries.append(source_to_bibtex(fm))

    if not entries:
        print("No sources found", file=sys.stderr)
        sys.exit(1)

    with open(output_file, "w") as f:
        f.write("\n\n".join(entries))
        f.write("\n")

    print(f"Exported {len(entries)} entries to {output_file}")


if __name__ == "__main__":
    main()
