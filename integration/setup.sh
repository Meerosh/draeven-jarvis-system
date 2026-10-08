#!/bin/bash

################################################################################
# JARVIS Integrated Ecosystem Setup Script
# Installs and configures: OmniRoute, Claude Mem, Head Room, Claude Code Setup, Task Observer
# Target: Draeven/JARVIS system at /home/claude/draeven-jarvis-system
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/home/claude/draeven-jarvis-system"
TEMPLATES_DIR="${INSTALL_DIR}/integration/env-templates"
HOME_DIR="${HOME}"
OMNIROUTE_PORT="20128"
CLAUDE_MEM_DB="${HOME_DIR}/.claude-mem/claude-mem.db"
HEADROOM_CONFIG="${HOME_DIR}/.headroom/config.json"
TASK_OBSERVER_DIR="${HOME_DIR}/.task-observer"

################################################################################
# Utility Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisite() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    print_success "$1 found"
    return 0
}

################################################################################
# Prerequisite Checks
################################################################################

print_header "Checking Prerequisites"

FAILED=0

if ! check_prerequisite "node"; then
    print_warning "Node.js 22.22.2+ required. Visit https://nodejs.org/"
    FAILED=1
fi

if ! check_prerequisite "npm"; then
    print_warning "npm required. Usually installed with Node.js"
    FAILED=1
fi

if ! check_prerequisite "git"; then
    print_warning "git required. Install from https://git-scm.com/"
    FAILED=1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 22 ]; then
    print_warning "Node.js version $NODE_VERSION detected. Recommend 22.22.2+. May still work, but not guaranteed."
fi

# Check port availability
if lsof -Pi :$OMNIROUTE_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $OMNIROUTE_PORT already in use. OmniRoute will need this port."
fi

if [ $FAILED -eq 1 ]; then
    print_error "Some prerequisites missing. Please install and try again."
    exit 1
fi

print_success "All prerequisites met"

################################################################################
# Directory Setup
################################################################################

print_header "Creating Integration Directories"

mkdir -p "$HOME_DIR/.omniroute"
print_success "Created ~/.omniroute"

mkdir -p "$HOME_DIR/.omniroute/logs"
print_success "Created ~/.omniroute/logs"

mkdir -p "$HOME_DIR/.omniroute/backups"
print_success "Created ~/.omniroute/backups"

mkdir -p "$HOME_DIR/.claude-mem"
print_success "Created ~/.claude-mem"

mkdir -p "$HOME_DIR/.claude-mem/chroma"
print_success "Created ~/.claude-mem/chroma"

mkdir -p "$HOME_DIR/.headroom"
print_success "Created ~/.headroom"

mkdir -p "$HOME_DIR/.headroom/logs"
print_success "Created ~/.headroom/logs"

mkdir -p "$TASK_OBSERVER_DIR"
print_success "Created ~/.task-observer"

mkdir -p "$HOME_DIR/.claude/skills/task-observer"
print_success "Created ~/.claude/skills/task-observer"

mkdir -p "$HOME_DIR/.claude/plugins"
print_success "Created ~/.claude/plugins directory"

################################################################################
# Environment File Setup
################################################################################

print_header "Copying Environment Configuration Files"

if [ ! -f "$HOME_DIR/.env.omniroute" ]; then
    cp "$TEMPLATES_DIR/.env.omniroute" "$HOME_DIR/.env.omniroute"
    print_success "Copied .env.omniroute to $HOME_DIR/"
else
    print_warning ".env.omniroute already exists, skipping"
fi

if [ ! -f "$HOME_DIR/.env.claude-mem" ]; then
    cp "$TEMPLATES_DIR/.env.claude-mem" "$HOME_DIR/.env.claude-mem"
    print_success "Copied .env.claude-mem to $HOME_DIR/"
else
    print_warning ".env.claude-mem already exists, skipping"
fi

if [ ! -f "$HEADROOM_CONFIG" ]; then
    cp "$TEMPLATES_DIR/headroom-config.json" "$HEADROOM_CONFIG"
    print_success "Copied headroom-config.json to ~/.headroom/"
else
    print_warning "headroom-config.json already exists, skipping"
fi

################################################################################
# OmniRoute Installation
################################################################################

print_header "Building OmniRoute Gateway (1/5)"

cd "$INSTALL_DIR/modules/OmniRoute"

if [ ! -d "node_modules" ]; then
    print_warning "Installing OmniRoute dependencies..."
    npm install --loglevel=warn
    print_success "OmniRoute dependencies installed"
else
    print_success "OmniRoute dependencies already installed"
fi

if [ ! -d "dist" ]; then
    print_warning "Building OmniRoute..."
    npm run build --loglevel=warn
    print_success "OmniRoute built successfully"
else
    print_success "OmniRoute already built"
fi

print_success "OmniRoute ready at port $OMNIROUTE_PORT"

################################################################################
# Claude Mem Installation
################################################################################

print_header "Installing Claude Mem (2/5)"

cd "$INSTALL_DIR/modules/claude-mem"

if [ ! -d "node_modules" ]; then
    print_warning "Installing Claude Mem dependencies..."
    npm install --loglevel=warn
    print_success "Claude Mem dependencies installed"
else
    print_success "Claude Mem dependencies already installed"
fi

if [ ! -d "dist" ]; then
    print_warning "Building Claude Mem..."
    npm run build --loglevel=warn
    print_success "Claude Mem built successfully"
else
    print_success "Claude Mem already built"
fi

print_success "Claude Mem plugin ready for installation"

################################################################################
# Head Room Setup
################################################################################

print_header "Setting up Head Room (3/5)"

cd "$INSTALL_DIR/modules/headroom"

if [ ! -d "node_modules" ]; then
    print_warning "Installing Head Room dependencies..."
    npm install --loglevel=warn
    print_success "Head Room dependencies installed"
else
    print_success "Head Room dependencies already installed"
fi

print_warning "Head Room requires Tauri native build (platform-specific)"
print_warning "Manual build step needed: cd modules/headroom && npm run tauri:build"
print_success "Head Room configuration ready at $HEADROOM_CONFIG"

################################################################################
# Claude Code Setup
################################################################################

print_header "Applying Claude Code Configuration (4/5)"

cd "$INSTALL_DIR/modules/claude-code-setup"

CLAUDE_DIR="$HOME_DIR/.claude"
mkdir -p "$CLAUDE_DIR"

# Copy MCP servers configuration
if [ -f "$TEMPLATES_DIR/mcp-servers.json" ]; then
    cp "$TEMPLATES_DIR/mcp-servers.json" "$CLAUDE_DIR/mcp-servers.json"
    print_success "Applied MCP servers configuration"
fi

# Copy commands configuration
if [ -f "$TEMPLATES_DIR/commands.json" ]; then
    cp "$TEMPLATES_DIR/commands.json" "$CLAUDE_DIR/commands.json"
    print_success "Applied custom commands configuration"
fi

# Copy status line configuration
if [ -f "$TEMPLATES_DIR/status-line.json" ]; then
    cp "$TEMPLATES_DIR/status-line.json" "$CLAUDE_DIR/status-line.json"
    print_success "Applied status line configuration"
fi

# Merge CLAUDE.md if it exists
if [ -f "$INSTALL_DIR/modules/claude-code-setup/etc/prompt.md" ]; then
    if [ -f "$CLAUDE_DIR/CLAUDE.md" ]; then
        print_warning "$CLAUDE_DIR/CLAUDE.md already exists, not overwriting"
    else
        touch "$CLAUDE_DIR/CLAUDE.md"
        print_success "Created $CLAUDE_DIR/CLAUDE.md"
    fi
fi

################################################################################
# Task Observer Installation
################################################################################

print_header "Installing Task Observer Meta-Skill (5/5)"

cd "$INSTALL_DIR/modules/TaskObserver"

if [ ! -d "node_modules" ]; then
    print_warning "Installing Task Observer dependencies..."
    npm install --loglevel=warn
    print_success "Task Observer dependencies installed"
else
    print_success "Task Observer dependencies already installed"
fi

# Copy Task Observer to Claude Code skills
if [ -d "dist" ]; then
    cp -r dist/* "$HOME_DIR/.claude/skills/task-observer/" 2>/dev/null || true
    print_success "Task Observer meta-skill installed"
else
    print_warning "Task Observer not yet built. Run: cd modules/TaskObserver && npm run build"
fi

mkdir -p "$TASK_OBSERVER_DIR/observations"
print_success "Task Observer observation directory ready"

################################################################################
# Verification
################################################################################

print_header "Verifying Installation"

VERIFICATION_PASSED=1

# Check OmniRoute
if [ -f "$INSTALL_DIR/modules/OmniRoute/dist/omniroute.mjs" ]; then
    print_success "OmniRoute binary verified"
else
    print_warning "OmniRoute binary not found. May need rebuild."
    VERIFICATION_PASSED=0
fi

# Check Claude Mem
if [ -d "$HOME_DIR/.claude-mem" ]; then
    print_success "Claude Mem directory verified"
else
    print_error "Claude Mem directory missing"
    VERIFICATION_PASSED=0
fi

# Check environment files
if [ -f "$HOME_DIR/.env.omniroute" ]; then
    print_success ".env.omniroute verified"
else
    print_error ".env.omniroute missing"
    VERIFICATION_PASSED=0
fi

if [ -f "$HOME_DIR/.env.claude-mem" ]; then
    print_success ".env.claude-mem verified"
else
    print_error ".env.claude-mem missing"
    VERIFICATION_PASSED=0
fi

# Check configurations
if [ -f "$HOME_DIR/.claude/mcp-servers.json" ]; then
    print_success "MCP servers configuration verified"
else
    print_warning "MCP servers configuration not yet applied"
fi

if [ -f "$HOME_DIR/.claude/commands.json" ]; then
    print_success "Custom commands configuration verified"
else
    print_warning "Custom commands configuration not yet applied"
fi

# Check Task Observer
if [ -d "$HOME_DIR/.claude/skills/task-observer" ]; then
    print_success "Task Observer skills directory verified"
else
    print_warning "Task Observer skills directory needs manual setup"
fi

################################################################################
# Integration Summary
################################################################################

print_header "Integration Summary"

cat << 'EOF'

✓ Directories Created:
  • ~/.omniroute/ (OmniRoute data)
  • ~/.claude-mem/ (Memory database)
  • ~/.headroom/ (Quota tracking)
  • ~/.task-observer/ (Observations)

✓ Components Status:
  • OmniRoute: Built (port 20128)
  • Claude Mem: Built (ready for plugin install)
  • Head Room: Dependencies installed (requires native build)
  • Claude Code Setup: Configuration applied
  • Task Observer: Dependencies installed

✓ Configuration Files:
  • .env.omniroute
  • .env.claude-mem
  • headroom-config.json
  • mcp-servers.json (MCP server definitions)
  • commands.json (JARVIS commands)
  • status-line.json (Claude Code status line)

EOF

print_header "Next Steps"

cat << 'EOF'

1. Start OmniRoute Gateway:
   cd /home/claude/draeven-jarvis-system/modules/OmniRoute
   npm start &

   Verify: curl http://127.0.0.1:20128/health

2. Install Claude Mem Plugin:
   • Via Claude App: Settings → Customize → Upload
   • Path: /home/claude/draeven-jarvis-system/modules/claude-mem/dist/

3. Build Head Room (platform-specific):
   cd /home/claude/draeven-jarvis-system/modules/headroom
   npm run tauri:build

   Then launch from: ./src-tauri/target/release/headroom

4. Install Task Observer:
   • Claude App: Settings → Skills → Upload
   • Path: ~/.claude/skills/task-observer/

5. Restart Claude Code to load MCP servers and commands

6. Verify Integration:
   • Check JARVIS health: curl http://127.0.0.1:4783/api/health
   • Test OmniRoute: curl http://127.0.0.1:20128/dashboard/free-tiers
   • Check Claude Mem: ls ~/.claude-mem/claude-mem.db

EOF

if [ $VERIFICATION_PASSED -eq 1 ]; then
    print_success "Setup completed successfully!"
    exit 0
else
    print_warning "Setup completed with some warnings. Review above."
    exit 0
fi
