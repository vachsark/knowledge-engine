"""Shared frontmatter parser for source files (used by the export and viewer scripts)."""

import json
import re

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def parse_value(val):
    """Parse one frontmatter value: a quoted string, a [list], or a bare word."""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        # Arrays are written as JSON-style lists: ["Smith, John", "Doe, Jane"].
        # Parse them properly so commas inside quotes don't split a name in two.
        try:
            items = json.loads(val)
            if isinstance(items, list):
                return [str(v).strip() for v in items if str(v).strip()]
        except ValueError:
            pass
        quoted = re.findall(r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'', val)
        if quoted:
            return [(d or s).strip() for d, s in quoted if (d or s).strip()]
        return [v.strip() for v in val[1:-1].split(",") if v.strip()]
    if len(val) >= 2 and val[0] == val[-1] == '"':
        try:
            return json.loads(val)
        except ValueError:
            return val[1:-1]
    if len(val) >= 2 and val[0] == val[-1] == "'":
        return val[1:-1]
    return val


def parse_frontmatter(content):
    """Return (frontmatter dict, body) for a markdown file."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    fm = {}
    for line in match.group(1).split("\n"):
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, val = line.partition(":")
            fm[key.strip()] = parse_value(val)
    return fm, content[match.end():].strip()
