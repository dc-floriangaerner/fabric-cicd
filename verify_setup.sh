#!/bin/bash

echo "=================================="
echo "Fabric CI/CD Setup Verification"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verification function
verify() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# Check Python
echo "Checking Python installation..."
python3 --version > /dev/null 2>&1
verify "Python 3 is installed"
echo ""

# Check Node.js
echo "Checking Node.js installation..."
node --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    verify "Node.js is installed (required for MCP servers)"
else
    echo -e "${YELLOW}⚠${NC} Node.js not found (optional for local development, required for MCP servers)"
fi
echo ""

# Check required files
echo "Checking project files..."
[ -f "requirements.txt" ]
verify "requirements.txt exists"

[ -f "pyproject.toml" ]
verify "pyproject.toml exists"

[ -f ".mcp/config.json" ]
verify ".mcp/config.json exists"

[ -f ".github/workflows/ci.yml" ]
verify "CI workflow exists"

[ -f ".github/workflows/deploy-fabric.yml" ]
verify "Deployment workflow exists"

[ -f "README.md" ]
verify "README.md exists"

[ -f ".env.template" ]
verify ".env.template exists"

[ -f "setup.sh" ] && [ -x "setup.sh" ]
verify "setup.sh exists and is executable"

[ -f "LICENSE" ]
verify "LICENSE exists"

[ -f "CONTRIBUTING.md" ]
verify "CONTRIBUTING.md exists"
echo ""

# Validate JSON and TOML files
echo "Validating configuration files..."
python3 -c "import json; json.load(open('.mcp/config.json'))" > /dev/null 2>&1
verify ".mcp/config.json is valid JSON"

python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" > /dev/null 2>&1 || \
python3 -c "import toml; toml.load('pyproject.toml')" > /dev/null 2>&1
verify "pyproject.toml is valid TOML"
echo ""

# Check Python syntax
echo "Checking Python syntax..."
if [ -f "examples/fabric_example.py" ]; then
    python3 -m py_compile examples/fabric_example.py > /dev/null 2>&1
    verify "examples/fabric_example.py syntax is valid"
fi
echo ""

# Check for .env file
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${YELLOW}⚠${NC} .env file not found - copy .env.template to .env and configure it"
fi
echo ""

# Summary
echo "=================================="
echo "Verification Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. If you haven't already, copy .env.template to .env"
echo "2. Configure your credentials in .env"
echo "3. Run ./setup.sh to install dependencies"
echo "4. Add GitHub Secrets for CI/CD workflows"
echo ""
