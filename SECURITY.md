# Security and Privacy

## What this tool does

- Searches for academic papers using your AI CLI (Claude Code, Gemini CLI, or Codex)
- Saves paper citations as markdown files in this folder
- Generates HTML, BibTeX, and CSV exports from those files
- All processing happens on your computer

## What this tool does NOT do

- **No data collection.** Nothing is sent to us. We have no server, no analytics, no telemetry.
- **No API keys required.** The tool uses your existing CLI subscription. The optional paper checker (`verify-sources.py`) works best with a free OpenAlex key, which you keep on your computer. We never see your credentials.
- **Minimal network calls.** Most network activity comes from your AI CLI doing web searches. Our export and viewer scripts (frontmatter.py, export-bibtex.py, export-csv.py, generate-viewer.py) are fully offline. The one exception is `verify-sources.py`, which sends paper titles and DOIs (and your OpenAlex key, if you set one) to api.openalex.org to check that papers are real. It sends nothing else, and it only runs when you or the AI run it.
- **No file access outside this folder.** The AI CLI works within this project directory. It does not read your documents, emails, or other files.
- **No background processes.** Nothing runs when you're not using it.

## The install script

The one-line installer (`install.sh`) does exactly three things:

1. Checks if Node.js is installed — installs it via your system package manager if not
2. Asks which AI CLI you want — installs it via npm
3. Clones this repo to `~/knowledge-engine`

You can (and should) read it before running it: [install.sh](install.sh)

If you don't trust the installer, use the manual setup steps in the README instead.

## Auditing the code

This is a small project. The complete list of our code:

| File | Lines | What it does |
|------|-------|-------------|
| `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` | ~160 | Instructions for the AI — tells it how to search and save papers |
| `.claude/agents/research-team.md` | ~100 | Research agent definition |
| `.claude/agents/research-critic.md` | ~35 | Citation verification agent |
| `.claude/agents/research-skeptic.md` | ~30 | Relevance review agent |
| `.claude/agents/research-analyzer.md` | ~50 | Cross-paper analysis agent |
| `scripts/frontmatter.py` | ~45 | Shared parser for source-file metadata (used by the three scripts below) |
| `scripts/export-bibtex.py` | ~110 | Reads source files, writes bibliography.bib |
| `scripts/export-csv.py` | ~60 | Reads source files, writes sources.csv |
| `scripts/verify-sources.py` | ~235 | Checks papers against OpenAlex (the only script that goes online) |
| `scripts/generate-viewer.py` | ~490 | Reads source files, generates index.html |
| `research.sh` | ~280 | Terminal runner (optional) |
| `install.sh` | ~140 | Installer (optional) |

Total: ~1,800 lines. You can read all of it in 15 minutes.

## Reporting issues

If you find a security concern, open an issue on GitHub or email the maintainer directly.
