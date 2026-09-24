#!/usr/bin/env python3
"""Check saved sources against OpenAlex, a free open catalog of scholarly papers.

For each source file it looks the paper up (by DOI, or by title when there is
no DOI) and reports whether the title, year, and first author match a real
record. This backs up the "no fake citations" rule with real data instead of
relying on the AI alone.

Usage:
    python3 scripts/verify-sources.py <sources-dir>            # report only
    python3 scripts/verify-sources.py <sources-dir> --fix      # also fill in blanks
    python3 scripts/verify-sources.py <sources-dir> --api-key YOUR_KEY

--fix only fills fields that are EMPTY (doi, year, journal, pdf_url) and
replaces "Abstract not available." with the real abstract. It never changes
a title or author list, and never deletes anything.

This is the only script here that goes online. It sends paper titles and DOIs
to api.openalex.org -- nothing else.

Since February 2026 OpenAlex asks for a free API key: without one you only get
a small daily test allowance. Get a key in about a minute at
https://openalex.org/settings/api, then pass --api-key or set the
OPENALEX_API_KEY environment variable.
"""

import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from frontmatter import FRONTMATTER_RE, parse_frontmatter

API = os.environ.get("KE_OPENALEX_URL", "https://api.openalex.org").rstrip("/")
FIELDS = "id,doi,title,publication_year,authorships,primary_location,open_access,abstract_inverted_index"
TITLE_MATCH = 0.9  # similarity needed to call two titles the same paper


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def title_similarity(a, b):
    return difflib.SequenceMatcher(None, " ".join(normalize(a)), " ".join(normalize(b))).ratio()


def last_name(author):
    """"Smith, John" -> smith; "John Smith" -> smith."""
    author = author.split(",")[0] if "," in author else (author.split() or [""])[-1]
    words = normalize(author)
    return words[-1] if words else ""


def clean_doi(doi):
    doi = str(doi or "").strip()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)


class OutOfCredits(Exception):
    """OpenAlex refused because the daily allowance is used up (or no key)."""


def fetch(path, params, api_key):
    params = dict(params, select=FIELDS)
    if api_key:
        params["api_key"] = api_key
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "knowledge-engine/verify-sources"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (401, 403, 409, 429):
            raise OutOfCredits(e.code) from None
        raise


def lookup(fm, api_key):
    """Return (OpenAlex work or None, how it was found)."""
    doi = clean_doi(fm.get("doi"))
    if doi:
        work = fetch(f"/works/doi:{urllib.parse.quote(doi, safe='/')}", {}, api_key)
        if work:
            return work, "doi"
    title = fm.get("title", "")
    # Strip characters that OpenAlex's filter syntax treats specially
    query = re.sub(r"[,:|]", " ", title.replace("[UNVERIFIED]", "")).strip()
    if not query:
        return None, "title"
    results = fetch("/works", {"filter": f"title.search:{query}", "per-page": 5}, api_key) or {}
    best = max(results.get("results", []), key=lambda w: title_similarity(title, w.get("title") or ""), default=None)
    if best and title_similarity(title, best.get("title") or "") >= TITLE_MATCH:
        return best, "title"
    return None, "title"


def compare(fm, work):
    """List of human-readable mismatches between a source file and the record."""
    problems = []
    title = fm.get("title", "").replace("[UNVERIFIED]", "").strip()
    if title_similarity(title, work.get("title") or "") < TITLE_MATCH:
        problems.append(f'title differs: record says "{work.get("title")}"')
    year, real_year = str(fm.get("year", "")).strip(), work.get("publication_year")
    # Allow one year of difference: online-first vs. print dates often differ
    if year.isdigit() and real_year and abs(int(year) - real_year) > 1:
        problems.append(f"year {year} but record says {real_year}")
    authors = fm.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    real = [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])]
    if authors and real and last_name(authors[0]) not in {last_name(r) for r in real}:
        problems.append(f'first author "{authors[0]}" not in record ({", ".join(real[:3])}...)')
    return problems


def rebuild_abstract(inverted):
    if not inverted:
        return ""
    positions = [(i, word) for word, idxs in inverted.items() for i in idxs]
    return " ".join(word for _, word in sorted(positions))


def set_field(content, key, value):
    """Set a frontmatter field, keeping every other line as written."""
    match = FRONTMATTER_RE.match(content)
    lines = match.group(1).split("\n")
    rendered = f"{key}: {value if isinstance(value, int) else json.dumps(value, ensure_ascii=False)}"
    for i, line in enumerate(lines):
        if line.split(":", 1)[0].strip() == key:
            lines[i] = rendered
            break
    else:
        lines.append(rendered)
    return "---\n" + "\n".join(lines) + "\n---\n" + content[match.end():]


def fill_blanks(path, content, fm, work):
    """Fill empty fields from the record. Returns (new content, list of changes)."""
    changes = []
    location = work.get("primary_location") or {}
    oa = work.get("open_access") or {}
    candidates = {
        "doi": clean_doi(work.get("doi")),
        "year": work.get("publication_year"),
        "journal": (location.get("source") or {}).get("display_name"),
        "pdf_url": oa.get("oa_url") or location.get("pdf_url"),
    }
    for key, value in candidates.items():
        if value and not str(fm.get(key, "")).strip():
            content = set_field(content, key, value)
            changes.append(key)

    abstract = rebuild_abstract(work.get("abstract_inverted_index"))
    section = re.search(r"(^## Abstract[ \t]*\n)(.*?)(?=^## |\Z)", content, re.M | re.S)
    if abstract and section and section.group(2).strip().lower().startswith("abstract not available"):
        content = content[:section.start(2)] + f"\n{abstract}\n\n" + content[section.end(2):]
        changes.append("abstract")

    if changes:
        path.write_text(content, encoding="utf-8")
    return changes


def main():
    args = sys.argv[1:]
    fix = "--fix" in args
    api_key = os.environ.get("OPENALEX_API_KEY", "")
    if "--api-key" in args:
        i = args.index("--api-key")
        api_key = args[i + 1] if i + 1 < len(args) else ""
        del args[i:i + 2]
    args = [a for a in args if a != "--fix"]
    sources_path = Path(args[0] if args else "sources")

    files = sorted(sources_path.glob("source-*.md"))
    if not files:
        print(f"No source files in {sources_path}", file=sys.stderr)
        sys.exit(1)

    counts = {"verified": 0, "mismatch": 0, "not found": 0, "error": 0}
    for md_file in files:
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(content)
        if not fm.get("title"):
            continue
        try:
            work, via = lookup(fm, api_key)
        except OutOfCredits as e:
            print(f"  ?  {md_file.name}: OpenAlex refused the request (HTTP {e}).")
            print("     The daily allowance is used up, or you need a free API key:")
            print("     https://openalex.org/settings/api  then re-run with --api-key YOUR_KEY")
            counts["error"] += len(files) - files.index(md_file)
            break
        except (urllib.error.URLError, OSError, ValueError) as e:
            counts["error"] += 1
            print(f"  ?  {md_file.name}: could not reach OpenAlex ({e})")
            continue
        finally:
            time.sleep(0.1)  # stay well under OpenAlex's rate limit

        if not work:
            counts["not found"] += 1
            print(f"  ✗  {md_file.name}: NOT FOUND by {via} -- check this paper exists")
            continue
        problems = compare(fm, work)
        status = "mismatch" if problems else "verified"
        counts[status] += 1
        mark = "!" if problems else "✓"
        print(f"  {mark}  {md_file.name}: {status.upper()} (matched by {via})")
        for p in problems:
            print(f"       - {p}")
        if fix:
            changes = fill_blanks(md_file, content, fm, work)
            if changes:
                print(f"       + filled in: {', '.join(changes)}")

    print()
    print(", ".join(f"{n} {k}" for k, n in counts.items()))
    if counts["error"]:
        print("Some lookups failed (network?). Re-run later to check those.")


if __name__ == "__main__":
    main()
