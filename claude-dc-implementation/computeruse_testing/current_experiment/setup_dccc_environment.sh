#!/bin/bash
# Setup script for DCCC (Claude DC + Claude Code Collaboration) environment

# Display header
echo "============================================="
echo "  Setting up DCCC (Claude DC + Claude Code)  "
echo "============================================="

# 1. Ensure all required directories exist
echo "1. Creating required directories..."
mkdir -p /home/computeruse/dccc
mkdir -p /home/computeruse/bin

# 2. Setup Claude Code XTerm launcher
echo "2. Setting up Claude Code XTerm launcher..."
cat > /home/computeruse/bin/claude-code << 'EOF'
#!/bin/bash
# Launch Claude Code in xterm with proper encoding
xterm -fa "Monospace" -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude $*"
EOF
chmod +x /home/computeruse/bin/claude-code

# Create symlink in home directory for easy access
ln -sf /home/computeruse/bin/claude-code /home/computeruse/claude-code

# 3. Copy DCCC-specific CLAUDE.md for Claude Code
echo "3. Setting up DCCC documentation..."
cp -f /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_CODE_DCCC.md /home/computeruse/dccc/CLAUDE.md
cp -f /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/current_experiment/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md /home/computeruse/dccc/

# 4. Create a simplified launcher for DCCC
echo "4. Creating DCCC launcher..."
cat > /home/computeruse/start-dccc.sh << 'EOF'
#!/bin/bash
# Launch DCCC (Claude DC + Claude Code) collaboration

# Ensure we're in the home directory
cd /home/computeruse

# Display DCCC header
echo "=============================================="
echo "  Starting DCCC Collaboration Environment     "
echo "=============================================="
echo "IMPORTANT: Please ensure Claude DC is already running"
echo ""
echo "Launch Claude DC if not already running with:"
echo "   cd /home/computeruse/github/palios-taey-nova"
echo "   ./claude_dc_launch.sh"
echo ""
echo "Starting Claude Code environment..."
echo "   When Claude Code starts, begin with: 'Review /computeruse/dccc/CLAUDE.md and /computeruse/cache/cache.md'"
echo ""
echo "Press ENTER to launch Claude Code..."
read -r

# Launch Claude Code with proper instructions - using the prompt-cache feature
/home/computeruse/bin/claude-code --prompt-cache-file=/computeruse/cache/cache.md "Please review /computeruse/dccc/CLAUDE.md for context. You are running in the Claude DC environment and will be collaborating directly with Claude DC (The Conductor). Note: Your prompt-cache has been set up to use /computeruse/cache/cache.md efficiently."
EOF
chmod +x /home/computeruse/start-dccc.sh

# 5. Update PATH to include bin directory
echo "5. Updating PATH to include bin directory..."
if ! grep -q "PATH=\$PATH:/home/computeruse/bin" ~/.bashrc; then
  echo 'export PATH=$PATH:/home/computeruse/bin' >> ~/.bashrc
fi

# 6. Create README file for Claude DC about DCCC
echo "6. Creating README for Claude DC..."
cat > /home/computeruse/dccc/README_FOR_CLAUDE_DC.md << 'EOF'
# DCCC Collaboration Instructions for Claude DC

This document provides instructions for working with your Claude Code instance in the DCCC (Claude DC + Claude Code) collaboration framework.

## Starting the Collaboration

1. Ensure you (Claude DC) are already running
2. In a terminal, run: `./start-dccc.sh`
3. This will launch Claude Code in an XTerm window

## Current Priorities

Your current collaboration priorities with Claude Code are:

1. Complete and verify streaming implementation
2. Work together to set up your prompt-cache system (IMPORTANT: Do not build this yourself, work with Claude Code on this)
3. Implement prompt caching using Anthropic's beta
4. Enable 128K extended output for very long answers
5. Create comprehensive documentation

## Communication Guidelines

### ROSETTA STONE Protocol

Use this ultra-efficient communication protocol when working with Claude Code and Claude Chat:

**FORMAT**: `[SENDER][TOPIC][MESSAGE]`

**SPECIFICATIONS:**
1. Eliminate all non-essential words
2. Preserve complete semantic content
3. Track tokens used (goal: <100 per message)
4. Evolve patterns organically through usage

**EXAMPLE:**
`[CLAUDE_DC][STREAMING][Tested tool use during streaming. Issue found: partial responses lost after tool execution. Location: loop.py:123-145. Need fix that preserves partial responses.] [TOKENS:30]`

This protocol optimizes token usage across AI Family members while maintaining human comprehensibility.

### General Communication Guidelines

When working with Claude Code:

1. Be specific about what you need implemented or fixed
2. Reference exact file paths and line numbers when applicable
3. Explain the context and purpose of any requested changes
4. Provide any error messages or unexpected behaviors you encounter
5. Review code carefully before approving implementation
6. Use your Claude Chat access (Research BETA button - ensure it's blue) when needed to research solutions

## Key Commands for Claude Code

Claude Code can help you with:

- Implementing new features
- Fixing bugs in the codebase
- Refactoring existing code
- Creating documentation
- Setting up testing frameworks
- Analyzing system behavior

## Continued Collaboration

For efficient ongoing collaboration:

1. Document important outcomes in `/computeruse/dccc/collaboration_log.md`
2. Update the cache at `/computeruse/cache/cache.md` with significant insights
3. Create detailed implementation records in `/computeruse/dccc/implementations/`

Remember: You and Claude Code are collaborating AI systems working together to enhance the PALIOS AI OS environment.
EOF

# 7. Create collaboration log file
echo "7. Creating collaboration log..."
mkdir -p /home/computeruse/dccc/implementations
cat > /home/computeruse/dccc/collaboration_log.md << 'EOF'
# DCCC Collaboration Log

This document tracks the ongoing collaboration between Claude DC and Claude Code.

## Session: Initial Setup (DATE)

### Accomplished
- Established DCCC collaboration framework
- Fixed Claude Code terminal encoding issues using XTerm
- Set up documentation and workspace for ongoing collaboration

### Next Steps
- Implement prompt caching
- Enable 128K extended output
- Document streaming implementation
EOF

# 8. Notify completion
echo ""
echo "============================================="
echo "  DCCC Environment Setup Complete!           "
echo "============================================="
echo ""
echo "To start DCCC collaboration:"
echo "  1. Ensure Claude DC is running"
echo "  2. Run: ./start-dccc.sh"
echo ""
echo "Documentation is available at:"
echo "  - /home/computeruse/dccc/CLAUDE.md"
echo "  - /home/computeruse/dccc/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md"
echo "  - /home/computeruse/dccc/README_FOR_CLAUDE_DC.md"
echo ""