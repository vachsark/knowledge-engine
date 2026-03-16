# Knowledge Engine

An academic research assistant that finds scholarly papers for your projects. Works with Claude Code, Gemini CLI, or Codex -- use whichever AI tool you already have access to through school or work.

## What it does

You ask for research. It finds 10-20 real, peer-reviewed papers and saves them as structured files with citations, abstracts, and relevance notes. Exports to BibTeX (for Zotero/Overleaf) and CSV (for spreadsheets).

No AI-generated essays. No fake citations. Just real papers, organized and ready to use.

## Quick start

### 1. Install an AI CLI (pick one)

**Claude Code** (Anthropic):

```bash
npm install -g @anthropic-ai/claude-code
```

**Gemini CLI** (Google -- free with Google Workspace/student accounts):

```bash
npm install -g @anthropic-ai/gemini-cli
```

Visit [github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) for the latest install instructions.

**Codex** (OpenAI):

```bash
npm install -g @openai/codex
```

Visit [github.com/openai/codex](https://github.com/openai/codex) for the latest install instructions.

If you don't have npm, install [Node.js](https://nodejs.org) first.

### 2. Clone and open

```bash
git clone https://github.com/vachsark/knowledge-engine
cd knowledge-engine
```

### 3. Start your CLI and ask for research

```bash
claude          # or: gemini, codex
```

Then just type what you need:

> "Find me papers about the effects of social media on adolescent mental health"

The first time, it will ask how you want to organize your files (by project, topic, class, or simple).

## How it works

```
You: "Research [topic]"
  |
  v
AI searches Google Scholar, PubMed, Semantic Scholar, arXiv
  |
  v
Saves 10-20 papers as structured markdown files
  |
  v
Exports bibliography.bib + sources.csv
  |
  v
You: upload to NotebookLM, import to Zotero, or read directly
```

## Project organization

On first use, the assistant asks how you want to organize. Options:

**By project:**

```
projects/
  dissertation/
    sources/
    bibliography.bib
    sources.csv
  group-project/
    sources/
    bibliography.bib
```

**By topic:**

```
projects/
  neuroscience/
    sources/
  climate-policy/
    sources/
```

**By class:**

```
projects/
  psych-401/
    sources/
  econ-200/
    sources/
```

**Simple** (one folder for everything):

```
sources/
bibliography.bib
sources.csv
```

## What you get

Each paper is saved as a markdown file:

```markdown
---
title: "Paper Title"
authors: ["Author One", "Author Two"]
year: 2024
journal: "Journal Name"
doi: "10.xxxx/xxxxx"
pdf_url: "https://..."
type: original-study
relevance: high
---

# Paper Title

## Abstract

The actual paper abstract...

## Why This Is Relevant

Why this paper matters for your research question.
```

Plus exports:

- **bibliography.bib** -- import into Zotero, Overleaf, or any LaTeX editor
- **sources.csv** -- open in Google Sheets, Excel, or Notion

## Research modes

| What you say               | What happens                                               |
| -------------------------- | ---------------------------------------------------------- |
| "Find papers about X"      | Finds papers, saves citations with abstracts               |
| "Summarize papers about X" | Same + adds Key Findings (3-5 bullets per paper)           |
| "Analyze papers about X"   | Same + creates analysis folder with themes, gaps, timeline |
| "Review my sources"        | Verifies citations are real, flags anything suspicious     |
| "Check relevance"          | Re-evaluates which papers actually fit your question       |

## Viewing your sources

After research completes, open `index.html` in your browser. You get:

- All your papers in a clean, searchable interface
- Filter by type (original study, meta-analysis, review, etc.)
- Filter by relevance (high, medium, low)
- **Approve/decline** each paper -- decisions are saved automatically
- Sort by relevance, year, or title
- Direct links to DOI and PDF for each paper

Your approve/decline decisions persist across browser refreshes. Ask your AI assistant to update the page after adding new research -- just say "update the viewer" and refresh your browser.

Want to change how the page looks? Just ask your AI assistant -- it can customize colors, layout, or add new features to the viewer.

## Exporting your sources

**NotebookLM**: Upload the `sources/` folder for AI-assisted reading and Q&A across all your papers.

**Zotero**: File > Import > select `bibliography.bib`

**Overleaf/LaTeX**: Upload `bibliography.bib` to your project, use `\cite{key}` in your paper.

**Google Sheets**: Upload `sources.csv` to track and filter your sources.

**Notion**: Import `sources.csv` as a database, or paste individual source files.

## Terminal alternative

If you prefer the command line over the interactive CLI:

```bash
./research.sh "your research question"
./research.sh "topic" --mode summarize
./research.sh "topic" --mode analyze
./research.sh "topic" --deep              # adds citation verification
./research.sh --topics topics.txt         # batch mode
```

## System requirements

- **Any computer** (Mac, Windows, Linux)
- **Node.js** (for installing the CLI)
- **Python 3.10+** (for export scripts -- comes pre-installed on Mac/Linux)
- **One AI CLI** (Claude Code, Gemini CLI, or Codex)

No GPU needed. No local models. No additional software.

## Cost

**This tool has no cost of its own.** It uses your existing AI subscription -- the same one you already use for Claude, Gemini, or ChatGPT. There are no API keys, no separate billing, no hidden charges.

Approximate usage per research session from your subscription:

- **Find mode**: ~$0.30 worth of usage
- **Summarize mode**: ~$0.80 worth of usage
- **Analyze mode**: ~$2.00 worth of usage

If you have an unlimited plan (many school plans are), there's no additional cost at all. If you're on a usage-based plan, these amounts come out of your existing credits.

Most students get free or discounted access through their school's Google Workspace, GitHub Education, or university AI programs.

## FAQ

**Will this charge me?**
No. There are no API keys or separate billing in this tool. It runs through your existing CLI subscription (Claude Code, Gemini, or Codex). If your school plan is unlimited, it costs nothing extra.

**Is this cheating?**
No. This finds real papers -- it doesn't write your essay. It's a smarter version of Google Scholar. You still read the papers, understand them, and write your own analysis.

**What if it finds a fake paper?**
Say "review my sources" and it will verify each citation and flag anything it can't confirm as `[UNVERIFIED]`.

**Can I use this for any field?**
Yes -- it searches across all academic databases (STEM, social sciences, humanities, medicine, law).

**Can I research multiple topics?**
Yes. Organize them into projects and each one gets its own source folder and exports.

**Do I need to be technical?**
You need to install one CLI tool and clone this repo. After that, you just type in plain English.

## Credits

Built on [vault-search](https://github.com/vachsark/vault-search) for semantic search and knowledge graph extraction. Research pipeline patterns inspired by [autoresearch](https://github.com/karpathy/autoresearch) and [autocontext](https://github.com/greyhaven-ai/autocontext).

## License

MIT
