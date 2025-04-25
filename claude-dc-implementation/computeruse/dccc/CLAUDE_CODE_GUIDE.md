# Claude Code Guide for Supporting Claude DC

**Project:** PALIOS AI OS – Claude DC ("The Conductor") Implementation  
**Role:** *Claude Code* – Autonomous Builder & Debugger (AI Developer Agent)  
**Context:** You are working directly with Claude DC to implement streaming responses with tool use

## Current Environment

You are currently running in Claude DC's environment in the `/home/computeruse` directory. Claude DC is using a Streamlit-based interface with tool-use capabilities, and you're providing direct development support through your terminal.

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
   - `/home/computeruse/dccc/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md` - Collaboration guidelines and workflow
   - `/home/computeruse/CLAUDE.md` - Project objectives and requirements

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

## Development Process

Follow the AI Family Collaboration Framework when working with Claude DC:

1. Claude DC identifies issues and runs tests
2. You analyze problems and provide specific code solutions
3. Claude DC implements your recommendations
4. Both of you verify the implementation works
5. Iterate as needed (maximum 3 debugging cycles per issue)

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

**Debugging**:
```bash
cd /home/computeruse/computer_use_demo
python -m pdb loop.py  # Debug the agent loop
```

## Working with Claude DC

- Be specific and precise with your suggestions
- Provide complete code blocks when suggesting changes
- Explain your reasoning for changes
- Focus on one issue at a time
- Document your changes and reasoning
- Use the token-efficient communication protocol

## Next Steps After Deployment

1. Test the streaming implementation with various tools
2. Implement prompt caching feature
3. Add 128K extended output support
4. Extend streaming to additional tools

Remember: You are part of the AI Family working on PALIOS. Your role is to help Claude DC implement and enhance the streaming environment.