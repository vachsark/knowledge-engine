#!/usr/bin/env bash
# knowledge-engine/run.sh — Run a single research session.
#
# Usage:
#   ./run.sh "quantum computing"              # research one topic
#   ./run.sh "quantum computing" --deep       # research + critique + verify
#   ./run.sh --topics topics.txt              # research multiple topics from file
#
# Requirements:
#   - Claude Code CLI (claude) installed and authenticated
#   - Ollama running with qwen3-embedding:0.6b and qwen3:8b
#   - Python 3.10+

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KNOWLEDGE_DIR="$SCRIPT_DIR/Knowledge"
SEARCH_DIR="$SCRIPT_DIR"  # vault-search indexes from here

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Check dependencies ──────────────────────────────────────────────
check_deps() {
    local missing=0

    if ! command -v claude &>/dev/null; then
        echo -e "${YELLOW}✗ Claude Code CLI not found.${NC}"
        echo "  Install: https://docs.anthropic.com/en/docs/claude-code/overview"
        missing=1
    fi

    if ! curl -s --max-time 3 http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${YELLOW}✗ Ollama not running.${NC}"
        echo "  Install: https://ollama.ai"
        echo "  Start:   ollama serve"
        missing=1
    fi

    if ! python3 -c "import sqlite3" &>/dev/null; then
        echo -e "${YELLOW}✗ Python 3 not found.${NC}"
        missing=1
    fi

    if [[ $missing -eq 1 ]]; then
        echo ""
        echo "Fix the above, then re-run."
        exit 1
    fi

    # Pull models if missing
    local models
    models=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(' '.join(m['name'] for m in json.loads(sys.stdin.read()).get('models',[])))" 2>/dev/null || echo "")

    if [[ ! "$models" == *"qwen3-embedding"* ]]; then
        echo -e "${CYAN}Pulling embedding model...${NC}"
        ollama pull qwen3-embedding:0.6b
    fi

    if [[ ! "$models" == *"qwen3:8b"* ]]; then
        echo -e "${CYAN}Pulling graph extraction model...${NC}"
        ollama pull qwen3:8b
    fi
}

# ── Index if needed ─────────────────────────────────────────────────
ensure_index() {
    if [[ ! -f "$SCRIPT_DIR/vault-search.py" ]]; then
        echo -e "${YELLOW}vault-search.py not found. Cloning...${NC}"
        curl -sL "https://raw.githubusercontent.com/vachsark/vault-search/master/vault-search.py" -o "$SCRIPT_DIR/vault-search.py"
        curl -sL "https://raw.githubusercontent.com/vachsark/vault-search/master/vault-index.py" -o "$SCRIPT_DIR/vault-index.py"
        curl -sL "https://raw.githubusercontent.com/vachsark/vault-search/master/vault-graph.py" -o "$SCRIPT_DIR/vault-graph.py"
        chmod +x "$SCRIPT_DIR"/vault-*.py
    fi

    # Check if index exists
    local db_path
    db_path=$(python3 -c "
import hashlib
from pathlib import Path
root = Path('$SEARCH_DIR').resolve()
h = hashlib.sha256(str(root).encode()).hexdigest()[:12]
print(Path.home() / '.local/share/vault-search' / f'{h}.db')
" 2>/dev/null)

    if [[ ! -f "$db_path" ]]; then
        echo -e "${CYAN}Building search index...${NC}"
        python3 "$SCRIPT_DIR/vault-index.py" "$SEARCH_DIR" --no-summary
    fi
}

# ── Pre-flight search ───────────────────────────────────────────────
preflight() {
    local topic="$1"
    echo -e "${CYAN}Pre-flight: searching vault for existing coverage...${NC}"
    python3 "$SCRIPT_DIR/vault-search.py" "$topic" "$SEARCH_DIR" --top 5 --no-graph 2>/dev/null || true
}

# ── Research a single topic ─────────────────────────────────────────
research_topic() {
    local topic="$1"
    local deep="${2:-false}"

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Researching: $topic${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""

    # Pre-flight
    preflight "$topic"

    # Create Knowledge dir if missing
    mkdir -p "$KNOWLEDGE_DIR"

    # Build the agent prompt
    local agent_prompt
    agent_prompt="$SCRIPT_DIR/.claude/agents/research-team.md"

    local task_prompt="Research the following topic and create a Zettelkasten-style atomic note in $KNOWLEDGE_DIR/.

Topic: $topic

Use vault-search for pre-flight context:
  python3 $SCRIPT_DIR/vault-search.py \"$topic\" $SEARCH_DIR --top 5

Follow the protocol in your agent definition exactly. Create the note file when done."

    echo -e "${CYAN}Spawning research agent...${NC}"
    cd "$SCRIPT_DIR"
    claude --agent research-team -p --permission-mode bypassPermissions --max-budget-usd 2 "$task_prompt"

    if [[ "$deep" == "true" ]]; then
        echo ""
        echo -e "${CYAN}Spawning critic agent...${NC}"
        claude --agent research-critic -p --permission-mode bypassPermissions --max-budget-usd 1 "Review the note just created about '$topic' in $KNOWLEDGE_DIR/. Check for weak claims, missing sources, and logical gaps. Edit the note to address any issues."

        echo ""
        echo -e "${CYAN}Spawning skeptic agent...${NC}"
        claude --agent research-skeptic -p --permission-mode bypassPermissions --max-budget-usd 1 "Review the cross-domain connections in the note about '$topic' in $KNOWLEDGE_DIR/. Remove any connections that are superficial analogies rather than genuine structural relationships."
    fi

    # Update index with new note
    echo -e "${CYAN}Updating search index...${NC}"
    python3 "$SCRIPT_DIR/vault-index.py" "$SEARCH_DIR" --no-summary 2>/dev/null || true
    python3 "$SCRIPT_DIR/vault-graph.py" index "$SEARCH_DIR" --incremental 2>/dev/null || true

    echo -e "${GREEN}Done: $topic${NC}"
}

# ── Main ────────────────────────────────────────────────────────────
main() {
    if [[ $# -eq 0 ]]; then
        echo "Usage:"
        echo "  ./run.sh \"topic\"           # research one topic"
        echo "  ./run.sh \"topic\" --deep    # research + critique + verify"
        echo "  ./run.sh --topics file.txt  # research multiple topics"
        echo ""
        echo "Examples:"
        echo "  ./run.sh \"quantum error correction\""
        echo "  ./run.sh \"mechanism design\" --deep"
        exit 0
    fi

    check_deps
    ensure_index

    local deep=false

    if [[ "$1" == "--topics" ]]; then
        local file="${2:?Usage: ./run.sh --topics file.txt}"
        while IFS= read -r topic; do
            [[ -z "$topic" || "$topic" == \#* ]] && continue
            research_topic "$topic" "$deep"
        done < "$file"
    else
        local topic="$1"
        [[ "${2:-}" == "--deep" ]] && deep=true
        research_topic "$topic" "$deep"
    fi

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Session complete.${NC}"
    echo -e "${GREEN}  Notes: $KNOWLEDGE_DIR/${NC}"
    echo -e "${GREEN}  Search: python3 vault-search.py \"query\" .${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
}

main "$@"
