#!/usr/bin/env bash
# research.sh — Academic research assistant.
# Finds papers, saves structured citations, optionally summarizes and analyzes.
#
# Usage:
#   ./research.sh "your research question"
#   ./research.sh "topic" --mode find        # just find papers (default)
#   ./research.sh "topic" --mode summarize   # find + summary per paper
#   ./research.sh "topic" --mode analyze     # find + summarize + themes + gaps
#   ./research.sh "topic" --deep             # + critic + skeptic review
#   ./research.sh --topics topics.txt        # batch from file
#
# Requirements:
#   - One of: Claude Code (claude), Gemini CLI (gemini), or OpenAI Codex (codex)
#   - Ollama (optional, for local search indexing)
#   - Python 3.10+

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCES_DIR="$SCRIPT_DIR/sources"
ANALYSIS_DIR="$SCRIPT_DIR/analysis"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# ── Detect CLI ──────────────────────────────────────────────────────
detect_cli() {
    if command -v claude &>/dev/null; then
        CLI="claude"
        CLI_NAME="Claude Code"
    elif command -v gemini &>/dev/null; then
        CLI="gemini"
        CLI_NAME="Gemini CLI"
    elif command -v codex &>/dev/null; then
        CLI="codex"
        CLI_NAME="Codex"
    else
        echo -e "${YELLOW}No AI CLI found.${NC}"
        echo ""
        echo "Install one of:"
        echo "  Claude Code:  https://docs.anthropic.com/en/docs/claude-code"
        echo "  Gemini CLI:   https://github.com/google-gemini/gemini-cli"
        echo "  Codex:        https://github.com/openai/codex"
        echo ""
        echo "Most students get free access through their school's Google Workspace or university subscription."
        exit 1
    fi
    echo -e "${DIM}Using: $CLI_NAME${NC}"
}

# ── Run agent via detected CLI ──────────────────────────────────────
run_agent() {
    local agent="$1"
    local prompt="$2"
    local budget="${3:-2}"

    cd "$SCRIPT_DIR"

    case "$CLI" in
        claude)
            claude --agent "$agent" -p --permission-mode bypassPermissions --max-budget-usd "$budget" "$prompt"
            ;;
        gemini)
            # Gemini CLI uses system prompt from agent file
            local agent_file="$SCRIPT_DIR/.claude/agents/${agent}.md"
            local system_prompt=""
            if [[ -f "$agent_file" ]]; then
                system_prompt=$(sed '1,/^---$/d; /^---$/,$d' "$agent_file" 2>/dev/null || cat "$agent_file")
            fi
            gemini -s "$system_prompt" "$prompt"
            ;;
        codex)
            local agent_file="$SCRIPT_DIR/.claude/agents/${agent}.md"
            if [[ -f "$agent_file" ]]; then
                codex --system-prompt "$(cat "$agent_file")" "$prompt"
            else
                codex "$prompt"
            fi
            ;;
    esac
}

# ── Check dependencies ──────────────────────────────────────────────
check_deps() {
    if ! python3 -c "import sqlite3" &>/dev/null; then
        echo -e "${YELLOW}Python 3 not found. Install Python 3.10+${NC}"
        exit 1
    fi

    # Ollama is optional — only needed for local search indexing
    HAS_OLLAMA=false
    if curl -s --max-time 3 http://localhost:11434/api/tags &>/dev/null; then
        HAS_OLLAMA=true

        # Pull small embedding model if missing
        local models
        models=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(' '.join(m['name'] for m in json.loads(sys.stdin.read()).get('models',[])))" 2>/dev/null || echo "")

        if [[ ! "$models" == *"qwen3-embedding"* ]]; then
            echo -e "${CYAN}Pulling embedding model (~400MB, one-time)...${NC}"
            ollama pull qwen3-embedding:0.6b
        fi
    fi
}

# ── Download vault-search tools if needed ───────────────────────────
ensure_tools() {
    if [[ ! -f "$SCRIPT_DIR/vault-search.py" ]]; then
        echo -e "${CYAN}Downloading search tools...${NC}"
        local base="https://raw.githubusercontent.com/vachsark/vault-search/master"
        curl -sL "$base/vault-search.py" -o "$SCRIPT_DIR/vault-search.py"
        curl -sL "$base/vault-index.py" -o "$SCRIPT_DIR/vault-index.py"
        curl -sL "$base/vault-graph.py" -o "$SCRIPT_DIR/vault-graph.py"
        chmod +x "$SCRIPT_DIR"/vault-*.py
    fi
}

# ── Build search index ──────────────────────────────────────────────
ensure_index() {
    [[ "$HAS_OLLAMA" == "false" ]] && return

    local db_path
    db_path=$(python3 -c "
import hashlib
from pathlib import Path
root = Path('$SCRIPT_DIR').resolve()
h = hashlib.sha256(str(root).encode()).hexdigest()[:12]
print(Path.home() / '.local/share/vault-search' / f'{h}.db')
" 2>/dev/null)

    if [[ ! -f "$db_path" ]] || [[ -d "$SOURCES_DIR" ]]; then
        python3 "$SCRIPT_DIR/vault-index.py" "$SCRIPT_DIR" --no-summary 2>/dev/null || true
    fi
}

# ── Pre-flight search ───────────────────────────────────────────────
preflight() {
    local topic="$1"
    if [[ "$HAS_OLLAMA" == "true" ]]; then
        echo -e "${DIM}Checking for existing sources on this topic...${NC}"
        python3 "$SCRIPT_DIR/vault-search.py" "$topic" "$SCRIPT_DIR" --top 3 --no-graph 2>/dev/null || true
    fi
}

# ── Cost estimate ───────────────────────────────────────────────────
estimate_cost() {
    local mode="$1"
    local deep="$2"
    local estimate=""

    case "$mode" in
        find)      estimate="~\$0.30" ;;
        summarize) estimate="~\$0.80" ;;
        analyze)   estimate="~\$2.00" ;;
    esac

    if [[ "$deep" == "true" ]]; then
        estimate="$estimate + ~\$1.00 for review"
    fi

    echo -e "${DIM}Estimated cost: $estimate of your $CLI_NAME credits${NC}"
}

# ── Research a single topic ─────────────────────────────────────────
research_topic() {
    local topic="$1"
    local mode="${2:-find}"
    local deep="${3:-false}"

    echo ""
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  Research: $topic${NC}"
    echo -e "${GREEN}${BOLD}  Mode: $mode${NC}"
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo ""

    estimate_cost "$mode" "$deep"
    echo ""

    # Pre-flight
    preflight "$topic"

    # Create output dirs
    mkdir -p "$SOURCES_DIR"

    # Count existing sources to set numbering
    local next_num
    next_num=$(( $(ls "$SOURCES_DIR"/source-*.md 2>/dev/null | wc -l) + 1 ))

    # Build the task prompt
    local mode_instructions=""
    case "$mode" in
        find)
            mode_instructions="For each paper, include: title, authors, year, journal, abstract, DOI, and PDF link if available. Do NOT include Key Findings or Methodology sections."
            ;;
        summarize)
            mode_instructions="For each paper, include: title, authors, year, journal, abstract, DOI, PDF link, AND a Key Findings section with 3-5 bullet points of the most important results."
            ;;
        analyze)
            mode_instructions="For each paper, include: title, authors, year, journal, abstract, DOI, PDF link, Key Findings (3-5 bullets), AND a brief Methodology section. After finding all sources, also create analysis files."
            ;;
    esac

    local task_prompt="You are an academic research assistant. Find scholarly papers and original studies for the following research question:

Research Question: $topic

Instructions:
1. Search for papers using WebSearch. Target: Google Scholar, Semantic Scholar, arXiv, PubMed, and relevant academic databases.
2. Find at least 10-15 relevant papers. Prioritize:
   - Original studies with empirical data
   - Foundational/seminal papers in the field
   - Recent meta-analyses and systematic reviews
   - Cross-disciplinary work that offers unique perspectives
3. For each paper, create a file in $SOURCES_DIR/ named source-NNN.md (starting from source-$(printf '%03d' $next_num).md)
4. $mode_instructions

Each source file MUST use this exact format:

---
title: \"Paper Title\"
authors: [\"Author1\", \"Author2\"]
year: 2024
journal: \"Journal Name\"
doi: \"10.xxxx/xxxxx\"
pdf_url: \"https://...\"
type: original-study
relevance: high
research_question: \"$topic\"
---

# Paper Title

## Abstract
<the paper's abstract>

## Why This Is Relevant
<1-2 sentences on why this paper matters for the research question>

Valid types: original-study, meta-analysis, systematic-review, review, foundational, book-chapter
Valid relevance: high, medium, low

IMPORTANT: Only include real papers with real DOIs. Do not fabricate citations. If you can't find a DOI, leave the field empty. If you're unsure about details, note that in the file."

    if [[ "$HAS_OLLAMA" == "true" ]]; then
        task_prompt="$task_prompt

You can check what's already been found with:
  python3 $SCRIPT_DIR/vault-search.py \"$topic\" $SCRIPT_DIR --top 5 --no-graph"
    fi

    echo -e "${CYAN}Finding papers...${NC}"
    run_agent "research-team" "$task_prompt" 2

    # Deep mode: critic + skeptic
    if [[ "$deep" == "true" ]]; then
        echo ""
        echo -e "${CYAN}Reviewing source quality...${NC}"
        run_agent "research-critic" "Review all source files in $SOURCES_DIR/. For each source: verify the citation details are plausible, check that the abstract matches the title, and flag any that look fabricated with [UNVERIFIED] in the title. Edit files directly." 1

        echo ""
        echo -e "${CYAN}Checking relevance...${NC}"
        run_agent "research-skeptic" "Review the 'Why This Is Relevant' section in each source file in $SOURCES_DIR/. Change relevance to 'low' for any paper that isn't genuinely useful for the research question: '$topic'. Be strict — only 'high' relevance papers should directly address the core question." 1
    fi

    # Analysis mode: generate cross-paper analysis
    if [[ "$mode" == "analyze" ]]; then
        mkdir -p "$ANALYSIS_DIR"
        echo ""
        echo -e "${CYAN}Analyzing across papers...${NC}"
        run_agent "research-analyzer" "Read all source files in $SOURCES_DIR/ about '$topic'. Create the following analysis files in $ANALYSIS_DIR/:

1. themes.md — Major themes and patterns across the papers. Group related findings.
2. gaps.md — What the literature doesn't cover. What questions remain unanswered?
3. timeline.md — How has understanding of this topic evolved? Key milestones by year.
4. methodology-summary.md — What research methods are used? What are the strengths and limitations?

Each file should cite specific papers by title and be useful for a literature review." 2
    fi

    # Run exports if sources exist
    if ls "$SOURCES_DIR"/source-*.md &>/dev/null; then
        echo ""
        echo -e "${CYAN}Generating exports...${NC}"
        python3 "$SCRIPT_DIR/scripts/export-bibtex.py" "$SOURCES_DIR" 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} bibliography.bib" || true
        python3 "$SCRIPT_DIR/scripts/export-csv.py" "$SOURCES_DIR" 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} sources.csv" || true
    fi

    # Update search index if Ollama is available
    if [[ "$HAS_OLLAMA" == "true" ]]; then
        echo -e "${DIM}Updating search index...${NC}"
        python3 "$SCRIPT_DIR/vault-index.py" "$SCRIPT_DIR" --no-summary 2>/dev/null || true
    fi

    local source_count
    source_count=$(ls "$SOURCES_DIR"/source-*.md 2>/dev/null | wc -l)
    echo ""
    echo -e "${GREEN}${BOLD}Done! Found $source_count sources.${NC}"
}

# ── Main ────────────────────────────────────────────────────────────
main() {
    if [[ $# -eq 0 ]]; then
        echo -e "${BOLD}Academic Research Assistant${NC}"
        echo ""
        echo "Usage:"
        echo "  ./research.sh \"your research question\""
        echo "  ./research.sh \"topic\" --mode summarize     # include key findings"
        echo "  ./research.sh \"topic\" --mode analyze       # full analysis"
        echo "  ./research.sh \"topic\" --deep               # + quality review"
        echo "  ./research.sh --topics topics.txt            # batch mode"
        echo ""
        echo "Modes:"
        echo "  find       Find papers and save citations (default, lightest)"
        echo "  summarize  Find + key findings per paper"
        echo "  analyze    Find + summarize + cross-paper themes and gaps"
        echo ""
        echo "Output:"
        echo "  sources/          Individual paper files (markdown)"
        echo "  bibliography.bib  BibTeX export (for LaTeX/Zotero)"
        echo "  sources.csv       Spreadsheet export"
        echo "  analysis/         Cross-paper analysis (analyze mode only)"
        exit 0
    fi

    detect_cli
    check_deps
    ensure_tools

    local mode="find"
    local deep=false
    local topic=""
    local topics_file=""

    # Parse args
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --mode)     mode="$2"; shift 2 ;;
            --deep)     deep=true; shift ;;
            --topics)   topics_file="$2"; shift 2 ;;
            *)          topic="$1"; shift ;;
        esac
    done

    ensure_index

    if [[ -n "$topics_file" ]]; then
        while IFS= read -r t; do
            [[ -z "$t" || "$t" == \#* ]] && continue
            research_topic "$t" "$mode" "$deep"
        done < "$topics_file"
    elif [[ -n "$topic" ]]; then
        research_topic "$topic" "$mode" "$deep"
    else
        echo "Error: provide a topic or --topics file"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Your sources are in: ${BOLD}sources/${NC}"
    echo -e "${GREEN}  BibTeX export:       ${BOLD}bibliography.bib${NC}"
    echo -e "${GREEN}  Spreadsheet:         ${BOLD}sources.csv${NC}"
    if [[ "$mode" == "analyze" ]]; then
        echo -e "${GREEN}  Analysis:            ${BOLD}analysis/${NC}"
    fi
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${DIM}Tip: Upload sources/ to NotebookLM for AI-assisted reading${NC}"
    echo -e "${DIM}Tip: Import bibliography.bib into Zotero or Overleaf${NC}"
}

main "$@"
