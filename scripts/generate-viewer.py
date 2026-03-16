#!/usr/bin/env python3
"""Generate a local HTML viewer for research sources.

Reads all source files from a directory and creates an index.html
that displays papers with filtering, sorting, and links.
No server needed -- just open the file in a browser.
"""

import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm = {}
    for line in content[3:end].strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            fm[key] = val
    body = content[end + 3:].strip()
    return fm, body


def extract_section(body, heading):
    """Extract content under a markdown heading."""
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_html(sources_dir, output_path):
    sources_path = Path(sources_dir)
    if not sources_path.exists():
        print(f"No sources directory: {sources_dir}", file=sys.stderr)
        sys.exit(1)

    papers = []
    for md_file in sorted(sources_path.glob("source-*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(content)
        if not fm.get("title"):
            continue

        authors = fm.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]

        abstract = extract_section(body, "Abstract")
        relevance_note = extract_section(body, "Why This Is Relevant")
        key_findings = extract_section(body, "Key Findings")
        citation_chain = extract_section(body, "Citation Chain")

        # Parse cites/cited_by arrays
        cites = fm.get("cites", [])
        cited_by = fm.get("cited_by", [])
        if isinstance(cites, str):
            cites = [c.strip() for c in cites.strip("[]").split(",") if c.strip()]
        if isinstance(cited_by, str):
            cited_by = [c.strip() for c in cited_by.strip("[]").split(",") if c.strip()]

        papers.append({
            "file": md_file.name,
            "title": fm.get("title", ""),
            "authors": authors,
            "year": fm.get("year", ""),
            "journal": fm.get("journal", ""),
            "doi": fm.get("doi", ""),
            "pdf_url": fm.get("pdf_url", ""),
            "type": fm.get("type", ""),
            "relevance": fm.get("relevance", ""),
            "research_question": fm.get("research_question", ""),
            "discovered_via": fm.get("discovered_via", "direct"),
            "cites": cites,
            "cited_by": cited_by,
            "abstract": abstract,
            "relevance_note": relevance_note,
            "key_findings": key_findings,
            "citation_chain": citation_chain,
        })

    if not papers:
        print("No sources found", file=sys.stderr)
        sys.exit(1)

    # Build papers JSON for embedding
    import json
    papers_json = json.dumps(papers, indent=2)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research Sources</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #0a0a0a; color: #e4e4e7;
  line-height: 1.6; padding: 20px;
  max-width: 1100px; margin: 0 auto;
}
a { color: #60a5fa; text-decoration: none; }
a:hover { text-decoration: underline; }

.header { margin-bottom: 30px; }
.header h1 { font-size: 28px; color: #fafafa; margin-bottom: 6px; }
.header .subtitle { color: #a1a1aa; font-size: 14px; }
.stats { display: flex; gap: 20px; margin-top: 12px; font-size: 13px; color: #71717a; }
.stats span { background: #18181b; padding: 4px 10px; border-radius: 6px; }

.controls {
  display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;
}
.controls input, .controls select {
  background: #18181b; border: 1px solid #27272a; color: #e4e4e7;
  padding: 8px 12px; border-radius: 6px; font-size: 13px;
}
.controls input { flex: 1; min-width: 200px; }
.controls select { min-width: 140px; }
.controls input:focus, .controls select:focus {
  outline: none; border-color: #60a5fa;
}

.paper {
  background: #18181b; border: 1px solid #27272a; border-radius: 8px;
  padding: 20px; margin-bottom: 12px; transition: border-color 0.2s;
}
.paper:hover { border-color: #3f3f46; }
.paper.declined { opacity: 0.4; }

.paper-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.paper-title { font-size: 16px; font-weight: 600; color: #fafafa; margin-bottom: 4px; }
.paper-meta { font-size: 13px; color: #a1a1aa; margin-bottom: 8px; }
.paper-meta .year { color: #60a5fa; font-weight: 500; }
.paper-meta .journal { font-style: italic; }

.badges { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.badge {
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500;
}
.badge.type { background: #1e1b4b; color: #818cf8; }
.badge.relevance-high { background: #052e16; color: #4ade80; }
.badge.relevance-medium { background: #422006; color: #fb923c; }
.badge.relevance-low { background: #450a0a; color: #f87171; }
.badge.discovered-direct { background: #1e293b; color: #94a3b8; }
.badge.discovered-reference { background: #172554; color: #60a5fa; }
.badge.discovered-cited-by { background: #4a1d96; color: #c084fc; }

.citation-links { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.citation-link {
  font-size: 11px; padding: 2px 8px; border-radius: 4px;
  background: #27272a; color: #a1a1aa; cursor: pointer; border: none;
}
.citation-link:hover { background: #3f3f46; color: #e4e4e7; }
.citation-link.cites { border-left: 2px solid #60a5fa; }
.citation-link.cited-by { border-left: 2px solid #c084fc; }

.section { margin-top: 10px; }
.section-label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
  color: #71717a; margin-bottom: 4px; font-weight: 600;
}
.section-content { font-size: 14px; color: #d4d4d8; }
.section-content.abstract { font-size: 13px; color: #a1a1aa; }

.links { display: flex; gap: 12px; margin-top: 12px; font-size: 13px; }
.links a {
  padding: 4px 10px; background: #27272a; border-radius: 4px; color: #60a5fa;
}
.links a:hover { background: #3f3f46; text-decoration: none; }

.actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn {
  padding: 6px 12px; border-radius: 6px; border: 1px solid #27272a;
  background: #18181b; color: #a1a1aa; cursor: pointer; font-size: 12px;
  transition: all 0.15s;
}
.btn:hover { border-color: #3f3f46; color: #e4e4e7; }
.btn.approved { background: #052e16; border-color: #166534; color: #4ade80; }
.btn.declined { background: #450a0a; border-color: #991b1b; color: #f87171; }

.empty { text-align: center; padding: 60px 20px; color: #71717a; }

.footer {
  margin-top: 40px; padding-top: 20px; border-top: 1px solid #27272a;
  font-size: 12px; color: #52525b; text-align: center;
}
</style>
</head>
<body>

<div class="header">
  <h1>Research Sources</h1>
  <p class="subtitle">Generated by <a href="https://github.com/vachsark/knowledge-engine">Knowledge Engine</a></p>
  <div class="stats">
    <span id="total-count"></span>
    <span id="type-breakdown"></span>
    <span id="approved-count"></span>
  </div>
</div>

<div class="controls">
  <input type="text" id="search" placeholder="Search papers..." />
  <select id="filter-type"><option value="">All types</option></select>
  <select id="filter-relevance">
    <option value="">All relevance</option>
    <option value="high">High</option>
    <option value="medium">Medium</option>
    <option value="low">Low</option>
  </select>
  <select id="filter-status">
    <option value="">All</option>
    <option value="approved">Approved</option>
    <option value="declined">Declined</option>
    <option value="pending">Pending</option>
  </select>
  <select id="filter-discovery">
    <option value="">All sources</option>
    <option value="direct">Direct search</option>
    <option value="reference">Found in references</option>
    <option value="cited-by">Found via "cited by"</option>
  </select>
  <select id="sort-by">
    <option value="relevance">Sort: Relevance</option>
    <option value="year-desc">Sort: Newest</option>
    <option value="year-asc">Sort: Oldest</option>
    <option value="title">Sort: Title</option>
  </select>
</div>

<div id="papers"></div>

<div class="footer">
  <p>Approve or decline papers, then click "Export Decisions" to save. Your AI assistant can read this file to learn your preferences.</p>
  <p>Ask your AI assistant to update this page after adding new research.</p>
  <button class="btn" onclick="exportDecisions()" style="margin-top:8px;">Export Decisions</button>
</div>

<script>
const papers = PAPERS_JSON_PLACEHOLDER;

// Load decisions from localStorage
const storageKey = 'ke-decisions-' + window.location.pathname;
let decisions = JSON.parse(localStorage.getItem(storageKey) || '{}');

function saveDecisions() {
  localStorage.setItem(storageKey, JSON.stringify(decisions));
  render();
}

function toggleDecision(file, status) {
  if (decisions[file] === status) {
    delete decisions[file];
  } else {
    decisions[file] = status;
  }
  saveDecisions();
}

function getFilteredPapers() {
  const search = document.getElementById('search').value.toLowerCase();
  const typeFilter = document.getElementById('filter-type').value;
  const relFilter = document.getElementById('filter-relevance').value;
  const statusFilter = document.getElementById('filter-status').value;
  const discoveryFilter = document.getElementById('filter-discovery').value;
  const sortBy = document.getElementById('sort-by').value;

  let filtered = papers.filter(p => {
    if (search && !p.title.toLowerCase().includes(search) &&
        !p.authors.join(' ').toLowerCase().includes(search) &&
        !p.abstract.toLowerCase().includes(search)) return false;
    if (typeFilter && p.type !== typeFilter) return false;
    if (relFilter && p.relevance !== relFilter) return false;
    if (discoveryFilter && (p.discovered_via || 'direct') !== discoveryFilter) return false;
    if (statusFilter) {
      const d = decisions[p.file] || 'pending';
      if (d !== statusFilter) return false;
    }
    return true;
  });

  filtered.sort((a, b) => {
    if (sortBy === 'year-desc') return (b.year || 0) - (a.year || 0);
    if (sortBy === 'year-asc') return (a.year || 0) - (b.year || 0);
    if (sortBy === 'title') return a.title.localeCompare(b.title);
    // Default: relevance (high > medium > low)
    const rel = { high: 3, medium: 2, low: 1 };
    return (rel[b.relevance] || 0) - (rel[a.relevance] || 0);
  });

  return filtered;
}

function render() {
  const filtered = getFilteredPapers();
  const container = document.getElementById('papers');

  // Stats
  const approved = Object.values(decisions).filter(d => d === 'approved').length;
  const declined = Object.values(decisions).filter(d => d === 'declined').length;
  document.getElementById('total-count').textContent = filtered.length + ' / ' + papers.length + ' papers';
  document.getElementById('approved-count').textContent = approved + ' approved, ' + declined + ' declined';

  // Type breakdown
  const typeCounts = {};
  papers.forEach(p => { typeCounts[p.type] = (typeCounts[p.type] || 0) + 1; });
  document.getElementById('type-breakdown').textContent =
    Object.entries(typeCounts).map(([t, c]) => c + ' ' + t).join(', ');

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty">No papers match your filters.</div>';
    return;
  }

  container.innerHTML = filtered.map(p => {
    const decision = decisions[p.file] || '';
    const isDeclined = decision === 'declined';
    const authorsStr = Array.isArray(p.authors) ? p.authors.join(', ') : (p.authors || 'Unknown');

    return '<div class="paper ' + (isDeclined ? 'declined' : '') + '" data-file="' + p.file + '">' +
      '<div class="paper-header">' +
        '<div>' +
          '<div class="paper-title">' + escapeHtml(p.title) + '</div>' +
          '<div class="paper-meta">' +
            '<span>' + escapeHtml(authorsStr) + '</span> ' +
            '<span class="year">(' + (p.year || 'n.d.') + ')</span> ' +
            (p.journal ? '<span class="journal">' + escapeHtml(p.journal) + '</span>' : '') +
          '</div>' +
        '</div>' +
        '<div class="actions">' +
          '<button class="btn ' + (decision === 'approved' ? 'approved' : '') + '" onclick="toggleDecision(\'' + p.file + '\', \'approved\')">Approve</button>' +
          '<button class="btn ' + (decision === 'declined' ? 'declined' : '') + '" onclick="toggleDecision(\'' + p.file + '\', \'declined\')">Decline</button>' +
        '</div>' +
      '</div>' +
      '<div class="badges">' +
        (p.type ? '<span class="badge type">' + p.type + '</span>' : '') +
        (p.relevance ? '<span class="badge relevance-' + p.relevance + '">' + p.relevance + ' relevance</span>' : '') +
        (p.discovered_via && p.discovered_via !== 'direct' ? '<span class="badge discovered-' + p.discovered_via + '">found via ' + p.discovered_via.replace('-', ' ') + '</span>' : '') +
      '</div>' +
      (p.relevance_note ? '<div class="section"><div class="section-label">Why Relevant</div><div class="section-content">' + escapeHtml(p.relevance_note) + '</div></div>' : '') +
      (p.citation_chain ? '<div class="section"><div class="section-label">Citation Chain</div><div class="section-content">' + escapeHtml(p.citation_chain) + '</div></div>' : '') +
      buildCitationLinks(p) +
      (p.abstract ? '<div class="section"><div class="section-label">Abstract</div><div class="section-content abstract">' + escapeHtml(p.abstract) + '</div></div>' : '') +
      (p.key_findings ? '<div class="section"><div class="section-label">Key Findings</div><div class="section-content">' + escapeHtml(p.key_findings) + '</div></div>' : '') +
      '<div class="links">' +
        (p.doi ? '<a href="https://doi.org/' + escapeHtml(p.doi) + '" target="_blank">DOI</a>' : '') +
        (p.pdf_url ? '<a href="' + escapeHtml(p.pdf_url) + '" target="_blank">PDF / Source</a>' : '') +
      '</div>' +
    '</div>';
  }).join('');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function buildCitationLinks(p) {
  const cites = p.cites || [];
  const citedBy = p.cited_by || [];
  if (cites.length === 0 && citedBy.length === 0) return '';

  let html = '<div class="section"><div class="section-label">Connected Papers</div><div class="citation-links">';

  cites.forEach(ref => {
    const linked = papers.find(pp => pp.file === ref + '.md' || pp.file === ref);
    const label = linked ? linked.title.substring(0, 40) + '...' : ref;
    html += '<button class="citation-link cites" onclick="scrollToSource(\'' + ref + '\')" title="This paper cites: ' + (linked ? escapeHtml(linked.title) : ref) + '">cites: ' + escapeHtml(label) + '</button>';
  });

  citedBy.forEach(ref => {
    const linked = papers.find(pp => pp.file === ref + '.md' || pp.file === ref);
    const label = linked ? linked.title.substring(0, 40) + '...' : ref;
    html += '<button class="citation-link cited-by" onclick="scrollToSource(\'' + ref + '\')" title="Cited by: ' + (linked ? escapeHtml(linked.title) : ref) + '">cited by: ' + escapeHtml(label) + '</button>';
  });

  html += '</div></div>';
  return html;
}

function exportDecisions() {
  const output = {
    exported_at: new Date().toISOString(),
    approved: [],
    declined: [],
    pending: []
  };
  papers.forEach(p => {
    const d = decisions[p.file];
    const entry = { file: p.file, title: p.title, year: p.year, doi: p.doi };
    if (d === 'approved') output.approved.push(entry);
    else if (d === 'declined') output.declined.push(entry);
    else output.pending.push(entry);
  });
  const blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'decisions.json';
  a.click();
  URL.revokeObjectURL(url);
}

function scrollToSource(ref) {
  const file = ref.endsWith('.md') ? ref : ref + '.md';
  const el = document.querySelector('[data-file="' + file + '"]');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.borderColor = '#60a5fa';
    setTimeout(() => { el.style.borderColor = ''; }, 2000);
  }
}

// Populate type filter
const types = [...new Set(papers.map(p => p.type).filter(Boolean))].sort();
const typeSelect = document.getElementById('filter-type');
types.forEach(t => {
  const opt = document.createElement('option');
  opt.value = t; opt.textContent = t;
  typeSelect.appendChild(opt);
});

// Event listeners
document.getElementById('search').addEventListener('input', render);
document.getElementById('filter-type').addEventListener('change', render);
document.getElementById('filter-relevance').addEventListener('change', render);
document.getElementById('filter-status').addEventListener('change', render);
document.getElementById('filter-discovery').addEventListener('change', render);
document.getElementById('sort-by').addEventListener('change', render);

render();
</script>
</body>
</html>"""

    html = html.replace("PAPERS_JSON_PLACEHOLDER", papers_json)

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Viewer created: {output_path} ({len(papers)} papers)")


def main():
    sources_dir = sys.argv[1] if len(sys.argv) > 1 else "sources"
    output_file = os.path.join(os.path.dirname(sources_dir) or ".", "index.html")
    generate_html(sources_dir, output_file)


if __name__ == "__main__":
    main()
