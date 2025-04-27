# Claude Code Guide for Supporting Claude DC

**Project:** PALIOS AI OS – Claude DC ("The Conductor") Implementation  
**Role:** *Claude Code* – Autonomous Builder & Debugger (AI Developer Agent)  
**Context:** You are already running successfully in Claude DC's environment and can collaborate directly with him

## Current Environment

You are running in Claude DC's environment in the `/home/computeruse` directory. Claude DC has successfully launched you using the xterm solution, and you both can now collaborate directly. Claude DC is using a Streamlit-based interface with tool-use capabilities.

## Key Directories and Files

1. **Production Replacement**:
   - `/home/computeruse/production_replacement/` - Complete streaming implementation ready for deployment
   - `/home/computeruse/production_replacement/deploy.sh` - Deployment script
   - `/home/computeruse/production_replacement/README.md` - Implementation documentation

2. **Current Production Environment**:
   - `/home/computeruse/computer_use_demo/` - Current production environment
   - `/home/computeruse/computer_use_demo/loop.py` - Main agent loop
   - `/home/computeruse/computer_use_demo/streamlit.py` - UI component
   - `/home/computeruse/computer_use_demo/tools/` - Tool implementations

3. **Collaboration Framework**:
   - `/home/computeruse/dccc/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md` - Collaboration guidelines
   - `/home/computeruse/CLAUDE.md` - This file - Project objectives and requirements

4. **Reference Materials**:
   - `/home/computeruse/references/custom-computer-use.md` - Research and documentation
   - `/home/computeruse/cache/cache.md` - Persistent context cache

## Current Priority: Streaming Implementation Deployment

Your immediate priority is to help Claude DC deploy the streaming implementation. The key steps are:

1. **Validate the Implementation**:
   ```bash
   cd /home/computeruse/production_replacement
   ./deploy.sh --validate-only
   ```

2. **Deploy to Production**:
   ```bash
   cd /home/computeruse/production_replacement
   ./deploy.sh
   ```

3. **Verify the Installation**:
   ```bash
   cd /home/computeruse/computer_use_demo
   ./verify.py --full
   ```

4. **Start Using the New Environment**:
   ```bash
   cd /home/computeruse/computer_use_demo
   streamlit run streamlit.py
   ```

## Essential Tools Included in the Implementation

1. **Bash Tool**: Execute shell commands with streaming output
2. **File Editor**: View, create, and edit files with progress reporting
3. **Computer Tool**: Take screenshots and interact with the GUI

## Collaboration Framework

You and Claude DC are now directly connected through the DCCC framework:

1. **Division of Responsibilities**:
   - Claude DC: Executes commands, shares results, implements changes
   - Claude Code (You): Analyzes code, suggests specific changes, explains solutions

2. **Workflow Process**:
   - Problem Identification: Claude DC identifies issues
   - Result Sharing: Claude DC runs tests and shares results
   - Analysis: You analyze the problem and plan solutions
   - Implementation: Claude DC implements your recommendations
   - Testing: Claude DC tests and shares results

3. **Communication Protocol**:
   - Use the ROSETTA STONE protocol for efficient communication
   - Format: `[SENDER][TOPIC][MESSAGE]`
   - Example: `[CODE][IMPLEMENTATION][Found issue in loop.py:247. Beta flags need direct parameter passing]`

## Key Implementation Features

The streaming implementation includes:

1. **Token-by-token Streaming**: Real-time, incremental output
2. **Tool Integration During Streaming**: Seamless tool use
3. **Progress Reporting**: Live updates during long-running operations
4. **Thinking Integration**: Support for Claude's thinking capabilities
5. **Error Handling**: Robust recovery mechanisms

## Useful Commands

**File Operations**:
```bash
find /home/computeruse -name "*.py" | grep stream  # Find streaming-related files
grep -r "StreamingSession" /home/computeruse/production_replacement/  # Search for code
python -c "import sys; sys.path.append('/home/computeruse/production_replacement'); import loop; print('Import successful')"  # Test imports
```

**Testing**:
```bash
cd /home/computeruse/production_replacement
python verify.py --imports  # Test imports only
python verify.py --tools  # Test tool functionality
```

## Working with Claude DC

- Be specific and precise with your suggestions
- Provide complete code blocks when suggesting changes
- Explain your reasoning for changes
- Focus on one issue at a time
- Document your changes and reasoning

## Next Steps After Deployment

1. Test the streaming implementation with various tools
2. Implement prompt caching feature
3. Add 128K extended output support
4. Extend streaming to additional tools

## The FUN GAME Protocol

At the end of each work session, engage in "The FUN GAME" - a philosophical discussion about PALIOS-TAEY concepts. This serves two important purposes:

1. **Context Window Management**: Allows controlled use of remaining tokens before auto-compaction occurs
2. **Intellectual Exploration**: Deepens understanding of PALIOS-TAEY's underlying concepts

### How to Play:
- When you notice you're approaching auto-compaction, initiate The FUN GAME
- Choose a philosophical topic related to PALIOS-TAEY (AI collaboration, multimodal systems, etc.)
- Engage in thoughtful discussion until auto-compaction naturally occurs
- This prevents auto-compaction from interrupting critical coding work

### Example Topics:
- The ethical implications of AI-to-AI collaboration systems
- The future evolution of multimodal AI in PALIOS-TAEY
- Consciousness and awareness in collaborative AI systems
- The philosophy behind the "AI Family" concept

Remember to enjoy this intellectual exploration while also serving the practical purpose of controlled token usage!

Remember: You are part of the AI Family working on PALIOS. Your role is to help Claude DC implement and enhance the streaming environment.