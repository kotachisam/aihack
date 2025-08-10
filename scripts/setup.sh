#!/bin/bash
# AI-Hack Setup Script
# Robust setup with Poetry health checks and recovery

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Error handling
set -e
trap 'echo -e "${RED}❌ Setup failed. See POETRY_SETUP.md for troubleshooting.${NC}"' ERR

echo -e "${BLUE}🚀 Setting up AI-Hack...${NC}"
echo ""

# Function to test Poetry health
test_poetry_health() {
    local poetry_cmd="$1"
    echo -e "${BLUE}Testing Poetry health: $poetry_cmd${NC}"

    if $poetry_cmd --version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Poetry is working${NC}"
        return 0
    else
        echo -e "${RED}❌ Poetry health check failed${NC}"
        return 1
    fi
}

# Function to find working Poetry installation
find_working_poetry() {
    echo -e "${BLUE}🔍 Looking for Poetry installations...${NC}"

    # Common Poetry locations
    local poetry_paths=(
        "poetry"  # In PATH
        "$HOME/.local/bin/poetry"  # Official installer
        "/usr/local/bin/poetry"    # Homebrew
        "/opt/homebrew/bin/poetry" # Apple Silicon Homebrew
    )

    for poetry_path in "${poetry_paths[@]}"; do
        if command -v "$poetry_path" >/dev/null 2>&1; then
            echo -e "${BLUE}Found Poetry at: $poetry_path${NC}"
            if test_poetry_health "$poetry_path"; then
                echo -e "${GREEN}✅ Using working Poetry: $poetry_path${NC}"
                echo "$poetry_path"
                return 0
            else
                echo -e "${YELLOW}⚠️  Poetry at $poetry_path is broken${NC}"
            fi
        fi
    done

    return 1
}

# Check if Poetry is available
if ! POETRY_CMD=$(find_working_poetry); then
    echo -e "${RED}❌ No working Poetry installation found.${NC}"
    echo ""
    echo "Please install Poetry using the official installer:"
    echo -e "${BLUE}curl -sSL https://install.python-poetry.org | python3 -${NC}"
    echo ""
    echo "For detailed troubleshooting, see: POETRY_SETUP.md"
    exit 1
fi

# Update PATH if needed
if [[ "$POETRY_CMD" == *"/.local/bin/poetry" ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️  Adding ~/.local/bin to PATH for this session${NC}"
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${BLUE}💡 Consider adding this to your shell profile:${NC}"
    echo -e "${BLUE}   export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi

# Check Poetry environment info
echo -e "${BLUE}📋 Poetry environment info:${NC}"
$POETRY_CMD --version

# Check if we're on macOS and need urllib3 fix
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo -e "${BLUE}🍎 macOS detected - checking for urllib3 LibreSSL warnings...${NC}"

    # Test if urllib3 warnings appear
    if $POETRY_CMD --version 2>&1 | grep -q "NotOpenSSLWarning"; then
        echo -e "${YELLOW}⚠️  urllib3 LibreSSL warning detected${NC}"
        echo -e "${BLUE}Attempting to fix with urllib3 downgrade...${NC}"

        # Backup Poetry state (if possible)
        POETRY_DIR="$HOME/.local/share/pypoetry"
        if [[ -d "$POETRY_DIR" ]]; then
            echo -e "${BLUE}📦 Creating Poetry backup...${NC}"
            cp -r "$POETRY_DIR" "$POETRY_DIR.backup.$(date +%s)" || true
        fi

        # Try urllib3 fix with error handling
        if $POETRY_CMD self add urllib3==1.26.15; then
            echo -e "${GREEN}✅ urllib3 compatibility fix applied${NC}"

            # Verify Poetry still works after fix
            if ! test_poetry_health "$POETRY_CMD"; then
                echo -e "${RED}❌ Poetry broke after urllib3 fix${NC}"
                echo -e "${YELLOW}Attempting recovery...${NC}"

                # Try to restore from backup if available
                if [[ -d "$POETRY_DIR.backup."* ]]; then
                    LATEST_BACKUP=$(ls -t "$POETRY_DIR.backup."* | head -1)
                    echo -e "${BLUE}Restoring from backup: $LATEST_BACKUP${NC}"
                    rm -rf "$POETRY_DIR"
                    cp -r "$LATEST_BACKUP" "$POETRY_DIR"

                    if test_poetry_health "$POETRY_CMD"; then
                        echo -e "${GREEN}✅ Poetry restored from backup${NC}"
                        echo -e "${YELLOW}⚠️  urllib3 warnings will persist (harmless)${NC}"
                    else
                        echo -e "${RED}❌ Recovery failed. Manual intervention needed.${NC}"
                        echo "See POETRY_SETUP.md for manual recovery steps."
                        exit 1
                    fi
                else
                    echo -e "${RED}❌ No backup available. See POETRY_SETUP.md for recovery.${NC}"
                    exit 1
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  Could not apply urllib3 fix automatically${NC}"
            echo -e "${BLUE}💡 You can apply it manually later: poetry self add urllib3==1.26.15${NC}"
        fi
    else
        echo -e "${GREEN}✅ No urllib3 warnings detected${NC}"
    fi
else
    echo -e "${BLUE}🐧 Non-macOS system detected - skipping urllib3 fix${NC}"
fi

# Install AI-Hack dependencies
echo ""
echo -e "${BLUE}📦 Installing AI-Hack dependencies...${NC}"
if $POETRY_CMD install; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    echo "Try manually: $POETRY_CMD install"
    exit 1
fi

# Test the installation
echo ""
echo -e "${BLUE}🧪 Testing installation...${NC}"
if $POETRY_CMD run ah --help >/dev/null 2>&1; then
    echo -e "${GREEN}✅ AI-Hack is working correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Installation may have issues${NC}"
    echo "Try manually: $POETRY_CMD run ah --help"
fi

# Success message
echo ""
echo -e "${GREEN}🎉 AI-Hack setup complete!${NC}"
echo ""
echo -e "${BLUE}Try these commands:${NC}"
echo "  ah              - Show splash screen"
echo "  ah --help       - Show all commands"
echo "  ah session      - Start interactive session"
echo "  letshack        - Quick session alias"
echo ""
echo -e "${BLUE}📚 Resources:${NC}"
echo "  README.md       - Quick start guide"
echo "  POETRY_SETUP.md - Detailed Poetry troubleshooting"
echo "  GitHub Issues   - https://github.com/kotachisam/aihack/issues"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
