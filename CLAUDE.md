# Academic Research Assistant

This project helps you find scholarly papers and original studies for your research.

## When the user asks to research a topic

1. **Find papers**: Use WebSearch to find scholarly sources (Google Scholar, Semantic Scholar, arXiv, PubMed)
2. **Save each source** as a file in `sources/` using the format below
3. **Export**: Run `python3 scripts/export-bibtex.py sources` and `python3 scripts/export-csv.py sources`
4. **Report**: Tell the user what you found and where the files are

## What to prioritize

- Original studies with empirical data
- Foundational/seminal papers
- Recent meta-analyses and systematic reviews
- Cross-disciplinary perspectives

Do NOT prioritize news articles, blog posts, or non-peer-reviewed content.

## Source file format

Save each paper as `sources/source-NNN.md`:

```markdown
---
title: "Exact Paper Title"
authors: ["First Author", "Second Author"]
year: 2024
journal: "Journal Name"
doi: "10.xxxx/xxxxx"
pdf_url: "https://..."
type: original-study
relevance: high
research_question: "the user's question"
---

# Exact Paper Title

## Abstract

<the paper's actual abstract>

## Why This Is Relevant

<1-2 sentences>
```

Valid types: `original-study`, `meta-analysis`, `systematic-review`, `review`, `foundational`, `book-chapter`

## Critical rules

- **NEVER fabricate citations.** Only include papers you found via search. Leave DOI empty if you can't find it.
- **NEVER invent abstracts.** Use the real abstract or write "Abstract not available."
- Find at least 10 sources per topic. Aim for 15-20.

## Modes (user can request)

| Request                    | What to do                                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------------------- |
| "find papers about X"      | Find + save citations (Abstract + Why Relevant only)                                               |
| "summarize papers about X" | Find + save + add Key Findings section (3-5 bullets)                                               |
| "analyze papers about X"   | Find + summarize + create `analysis/` with themes.md, gaps.md, timeline.md, methodology-summary.md |
| "review my sources"        | Use the `research-critic` agent to verify citations exist                                          |
| "check relevance"          | Use the `research-skeptic` agent to re-evaluate relevance ratings                                  |

## Available agents

- `research-team` — finds and saves papers (primary)
- `research-critic` — verifies citations are real, fixes errors
- `research-skeptic` — checks relevance ratings are accurate
- `research-analyzer` — cross-paper analysis (themes, gaps, timeline)

## Search index (optional, requires Ollama)

If the user has Ollama running, you can search existing sources:

```bash
python3 vault-search.py "query" . --top 5
```

This checks what's already been found to avoid duplicates.

## Exports

After finding sources, always run:

```bash
python3 scripts/export-bibtex.py sources    # → bibliography.bib
python3 scripts/export-csv.py sources       # → sources.csv
```

These let the user import into Zotero, Overleaf, Google Sheets, etc.

## Terminal alternative

Users can also run `./research.sh "topic"` from the terminal. This script automates the full flow including pre-flight search, agent invocation, and exports.
