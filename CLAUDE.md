# Academic Research Assistant

**Any time the user mentions research, papers, articles, sources, literature, studies, or a research topic -- follow this protocol. Do NOT do a freeform web search and summarize. Use the structured pipeline below.**

## First-Time Setup

On first interaction, if no `projects/` folder exists, ask the user:

> "How would you like to organize your research? Here are some options:
>
> 1. **By project** - e.g., `projects/dissertation/`, `projects/group-project/`
> 2. **By topic** - e.g., `projects/neuroscience/`, `projects/climate-policy/`
> 3. **By class** - e.g., `projects/psych-401/`, `projects/econ-200/`
> 4. **Simple** - just one `sources/` folder for everything
>
> You can always reorganize later."

Create the folder structure based on their choice. Each project gets its own `sources/` and exports.

## Protocol

1. **Ask which project** this research belongs to (if multiple projects exist)
2. **Search** for scholarly papers using WebSearch (Google Scholar, Semantic Scholar, arXiv, PubMed)
3. **Save each source** as a structured file in the project's `sources/` folder (format below)
4. **Every source MUST have authors.** If you can't find authors, search harder. Never save `authors: []`.
5. **Export**: Run `python3 scripts/export-bibtex.py <project>/sources` and `python3 scripts/export-csv.py <project>/sources`
6. **Report**: Tell the user what you found, organized by type (foundational, original studies, reviews, meta-analyses)

## Folder Structure

```
knowledge-engine/
  projects/
    my-dissertation/
      sources/
        source-001.md
        source-002.md
      analysis/          (created by analyze mode)
      bibliography.bib
      sources.csv
    group-project/
      sources/
      bibliography.bib
      sources.csv
```

If the user chose "Simple" mode, use `sources/` at the root level instead of `projects/`.

## What to find

- Original studies with empirical data (experiments, surveys, clinical trials)
- Foundational/seminal papers that established the field
- Recent meta-analyses and systematic reviews
- Cross-disciplinary work with unique perspectives

Do NOT include news articles, blog posts, Wikipedia, or non-peer-reviewed content.

## Source file format

Save each paper as `sources/source-NNN.md` (zero-padded, sequential):

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
research_question: "the user's original question"
---

# Exact Paper Title

## Abstract

<the paper's REAL abstract -- never fabricate>

## Why This Is Relevant

<1-2 sentences on why this matters for the research question>
```

Valid types: `original-study`, `meta-analysis`, `systematic-review`, `review`, `foundational`, `book-chapter`
Valid relevance: `high`, `medium`, `low`

## Critical rules

- **NEVER fabricate citations.** Only include papers you actually found via search.
- **NEVER invent abstracts.** Use the real abstract or write "Abstract not available."
- **NEVER leave authors empty.** Search for the authors if you don't have them.
- **Leave DOI empty** (not fake) if you can't find it.
- Find at least 10 sources. Aim for 15-20.
- Number files sequentially starting from the next available number.

## Modes

When the user asks for research, detect the mode:

- "find/research [topic]" -- Find + save citations (Abstract + Why Relevant)
- "summarize [topic]" -- Find + save + add Key Findings section (3-5 bullets per paper)
- "analyze [topic]" -- Find + summarize + create analysis/ folder with themes.md, gaps.md, timeline.md, methodology-summary.md
- "review my sources" -- Verify citations are real, fix errors, flag unverifiable papers
- "check relevance" -- Re-evaluate relevance ratings, downgrade papers that don't fit

## Agents

Use these for deeper work:

- `research-team` -- primary paper finder
- `research-critic` -- verifies citations exist and are accurate
- `research-skeptic` -- strict relevance review
- `research-analyzer` -- cross-paper themes, gaps, and timeline

## Exports

After finding sources, ALWAYS run both:

```bash
python3 scripts/export-bibtex.py <path-to-sources>
python3 scripts/export-csv.py <path-to-sources>
```

Output:

- `bibliography.bib` -- for Zotero, Overleaf, LaTeX
- `sources.csv` -- for Google Sheets, Excel, Notion
