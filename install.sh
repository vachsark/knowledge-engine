#!/usr/bin/env bash
# Knowledge Engine — One-line installer
# curl -sL https://raw.githubusercontent.com/vachsark/knowledge-engine/master/install.sh | bash

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

echo ""
echo -e "${GREEN}${BOLD}  Knowledge Engine — Academic Research Assistant${NC}"
echo -e "${DIM}  github.com/vachsark/knowledge-engine${NC}"
echo ""

# ── Check for git ───────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}git not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${CYAN}This will prompt you to install Xcode Command Line Tools. Click 'Install' when asked.${NC}"
        xcode-select --install 2>/dev/null || true
        echo -e "${YELLOW}After installation finishes, re-run this script.${NC}"
        exit 0
    elif command -v apt &>/dev/null; then
        sudo apt update && sudo apt install -y git
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm git
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git
    else
        echo -e "${YELLOW}Please install git: https://git-scm.com/downloads${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}  ✓ git found${NC}"

# ── Check for Node.js ───────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        if command -v brew &>/dev/null; then
            brew install node
        else
            echo -e "${CYAN}Installing Homebrew first...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install node
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y nodejs npm
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm nodejs npm
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y nodejs npm
        else
            echo -e "${YELLOW}Couldn't detect package manager. Install Node.js from https://nodejs.org${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Please install Node.js from https://nodejs.org then re-run this script.${NC}"
        exit 1
    fi

    if command -v node &>/dev/null; then
        echo -e "${GREEN}  ✓ Node.js installed ($(node --version))${NC}"
    else
        echo -e "${YELLOW}Node.js installation may need a terminal restart. Close and reopen your terminal, then re-run this script.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ Node.js found ($(node --version))${NC}"
fi

# ── Check for an AI CLI ─────────────────────────────────────────────
CLI_FOUND=false

if command -v claude &>/dev/null; then
    echo -e "${GREEN}  ✓ Claude Code found${NC}"
    CLI_FOUND=true
    CLI_NAME="claude"
elif command -v gemini &>/dev/null; then
    echo -e "${GREEN}  ✓ Gemini CLI found${NC}"
    CLI_FOUND=true
    CLI_NAME="gemini"
elif command -v codex &>/dev/null; then
    echo -e "${GREEN}  ✓ Codex found${NC}"
    CLI_FOUND=true
    CLI_NAME="codex"
fi

if [[ "$CLI_FOUND" == "false" ]]; then
    echo ""
    echo -e "${YELLOW}No AI CLI found. Which would you like to install?${NC}"
    echo ""
    echo "  1) Claude Code (Anthropic)"
    echo "  2) Gemini CLI  (Google — free with student accounts)"
    echo "  3) Codex       (OpenAI)"
    echo "  4) Skip — I'll install one myself"
    echo ""
    read -p "Choice [1-4]: " choice

    case "$choice" in
        1)
            echo -e "${CYAN}Installing Claude Code...${NC}"
            npm install -g @anthropic-ai/claude-code
            CLI_NAME="claude"
            ;;
        2)
            echo -e "${CYAN}Installing Gemini CLI...${NC}"
            npx https://github.com/google-gemini/gemini-cli
            CLI_NAME="gemini"
            ;;
        3)
            echo -e "${CYAN}Installing Codex...${NC}"
            npm install -g @openai/codex
            CLI_NAME="codex"
            ;;
        4)
            echo -e "${DIM}Skipping CLI install. Install one later and come back.${NC}"
            CLI_NAME="claude"
            ;;
        *)
            echo -e "${DIM}Skipping. Install a CLI later.${NC}"
            CLI_NAME="claude"
            ;;
    esac
fi

# ── Clone the repo ──────────────────────────────────────────────────
INSTALL_DIR="$HOME/knowledge-engine"

if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "${GREEN}  ✓ knowledge-engine already exists at $INSTALL_DIR${NC}"
    cd "$INSTALL_DIR"
    git pull --quiet 2>/dev/null || true
else
    echo -e "${CYAN}Cloning knowledge-engine...${NC}"
    git clone --quiet https://github.com/vachsark/knowledge-engine "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    echo -e "${GREEN}  ✓ Cloned to $INSTALL_DIR${NC}"
fi

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Setup complete!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  To start researching:"
echo ""
echo -e "    ${BOLD}cd ~/knowledge-engine${NC}"
echo -e "    ${BOLD}${CLI_NAME}${NC}"
echo ""
echo -e "  Then type:"
echo -e "    ${DIM}\"Read the project files, then find me papers about [your topic]\"${NC}"
echo ""
echo -e "  Your papers will appear in sources/ and you can"
echo -e "  open index.html in your browser to view them."
echo ""
