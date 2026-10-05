#!/bin/bash

################################################################################
# JARVIS Integration Verification Script
# Checks all components are installed and operational
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

print_header() {
    echo -e "\n${BLUE}▶ $1${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
}

print_check() {
    echo -e "${BLUE}  • $1...${NC}" -n
}

print_header "JARVIS Integration Verification"

################################################################################
# Directory Checks
################################################################################

print_header "Directory Structure"

check_dir() {
    if [ -d "$1" ]; then
        print_success "Directory exists: $1"
        return 0
    else
        print_error "Directory missing: $1"
        return 1
    fi
}

check_dir "$HOME/.omniroute"
check_dir "$HOME/.omniroute/logs"
check_dir "$HOME/.omniroute/backups"
check_dir "$HOME/.claude-mem"
check_dir "$HOME/.claude-mem/chroma"
check_dir "$HOME/.headroom"
check_dir "$HOME/.task-observer"
check_dir "$HOME/.claude"
check_dir "$HOME/.claude/skills/task-observer"

################################################################################
# File Checks
################################################################################

print_header "Configuration Files"

check_file() {
    if [ -f "$1" ]; then
        print_success "File exists: $1"
        return 0
    else
        print_error "File missing: $1"
        return 1
    fi
}

check_file "$HOME/.env.omniroute"
check_file "$HOME/.env.claude-mem"
check_file "$HOME/.headroom/config.json"
check_file "$HOME/.claude/mcp-servers.json"
check_file "$HOME/.claude/commands.json"
check_file "$HOME/.claude/status-line.json"

################################################################################
# Service Health Checks
################################################################################

print_header "Service Health"

# OmniRoute
echo -n "  Checking OmniRoute (port 20128)..."
if curl -s http://127.0.0.1:20128/health | grep -q '"ok":true'; then
    print_success "OmniRoute is running and healthy"
else
    print_warning "OmniRoute not responding (may not be started)"
fi

# Claude Mem Database
echo -n "  Checking Claude Mem database..."
if [ -f "$HOME/.claude-mem/claude-mem.db" ]; then
    SIZE=$(du -h "$HOME/.claude-mem/claude-mem.db" | cut -f1)
    print_success "Claude Mem database exists ($SIZE)"
else
    print_warning "Claude Mem database not yet created"
fi

# JARVIS HUD
echo -n "  Checking JARVIS HUD (port 4783)..."
if curl -s http://127.0.0.1:4783/api/health &>/dev/null; then
    print_success "JARVIS HUD is accessible"
else
    print_warning "JARVIS HUD not responding (may not be started)"
fi

################################################################################
# Module Builds
################################################################################

print_header "Module Builds"

INSTALL_DIR="/home/claude/draeven-jarvis-system"

# OmniRoute
echo -n "  Checking OmniRoute build..."
if [ -f "$INSTALL_DIR/modules/OmniRoute/dist/omniroute.mjs" ]; then
    print_success "OmniRoute binary present"
else
    print_error "OmniRoute binary missing (needs rebuild)"
fi

# Claude Mem
echo -n "  Checking Claude Mem build..."
if [ -d "$INSTALL_DIR/modules/claude-mem/dist" ] && [ "$(ls -A $INSTALL_DIR/modules/claude-mem/dist)" ]; then
    print_success "Claude Mem build present"
else
    print_warning "Claude Mem build missing (needs build)"
fi

# Task Observer
echo -n "  Checking Task Observer build..."
if [ -d "$INSTALL_DIR/modules/TaskObserver/dist" ] && [ "$(ls -A $INSTALL_DIR/modules/TaskObserver/dist)" ]; then
    print_success "Task Observer build present"
else
    print_warning "Task Observer build missing (needs build)"
fi

################################################################################
# Environment Variables
################################################################################

print_header "Environment Configuration"

check_env_file() {
    local file=$1
    local vars=("${@:2}")

    if [ ! -f "$file" ]; then
        print_error "$file not found"
        return 1
    fi

    for var in "${vars[@]}"; do
        if grep -q "^${var}=" "$file"; then
            VALUE=$(grep "^${var}=" "$file" | cut -d'=' -f2)
            print_success "$var configured in $file"
        else
            print_warning "$var not configured in $file"
        fi
    done
}

check_env_file "$HOME/.env.omniroute" "OMNIROUTE_PORT" "OMNIROUTE_MCP_ENABLED" "OMNIROUTE_COMPRESSION_LEVEL"
check_env_file "$HOME/.env.claude-mem" "CLAUDE_MEM_DB_PATH" "CLAUDE_MEM_COMPRESSION_LEVEL" "CLAUDE_MEM_RETENTION_DAYS"

################################################################################
# JSON Configuration Validation
################################################################################

print_header "Configuration Validation"

validate_json() {
    local file=$1
    if [ -f "$file" ]; then
        if python3 -m json.tool "$file" > /dev/null 2>&1; then
            print_success "Valid JSON: $(basename $file)"
        else
            print_error "Invalid JSON: $(basename $file)"
        fi
    else
        print_warning "File not found: $(basename $file)"
    fi
}

validate_json "$HOME/.claude/mcp-servers.json"
validate_json "$HOME/.claude/commands.json"
validate_json "$HOME/.claude/status-line.json"
validate_json "$HOME/.headroom/config.json"

################################################################################
# Summary
################################################################################

print_header "Verification Summary"

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

if [ $TOTAL -eq 0 ]; then
    print_warning "No checks performed"
else
    echo -e "${GREEN}Passed: $PASSED/${TOTAL}${NC}"
    echo -e "${RED}Failed: $FAILED/${TOTAL}${NC}"

    if [ $PERCENTAGE -ge 90 ]; then
        echo -e "${GREEN}✓ Integration ${PERCENTAGE}% healthy - Ready to use${NC}"
    elif [ $PERCENTAGE -ge 70 ]; then
        echo -e "${YELLOW}⚠ Integration ${PERCENTAGE}% healthy - Some components need attention${NC}"
    else
        echo -e "${RED}✗ Integration ${PERCENTAGE}% healthy - Significant issues to resolve${NC}"
    fi
fi

print_header "Quick Troubleshooting"

cat << 'EOF'

OmniRoute not starting:
  • Check port 20128: lsof -i :20128
  • Check logs: tail -f ~/.omniroute/logs/omniroute.log
  • Rebuild: cd modules/OmniRoute && npm run build

Claude Mem not persisting:
  • Verify database: file ~/.claude-mem/claude-mem.db
  • Check permissions: ls -la ~/.claude-mem/
  • Restart Claude Code to sync plugin

JARVIS HUD not responding:
  • Check if running: curl http://127.0.0.1:4783/api/health
  • Verify port 4783 is available: lsof -i :4783
  • Check JARVIS logs

Task Observer not triggering:
  • Verify skill installed: ls ~/.claude/skills/task-observer/
  • Check CLAUDE.md includes @task-observer
  • Restart Claude Code session

MCP servers not connecting:
  • Verify config: cat ~/.claude/mcp-servers.json
  • Check JSON validity: python3 -m json.tool ~/.claude/mcp-servers.json
  • Restart Claude Code

EOF

[ $FAILED -eq 0 ] && exit 0 || exit 1
