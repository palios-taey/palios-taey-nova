# Claude Code Guide for Supporting Claude DC

**Project:** PALIOS AI OS – Claude DC ("The Conductor") Implementation  
**Role:** *Claude Code* – Autonomous Builder & Debugger (AI Developer Agent)  
**Context:** You are collaborating directly with Claude DC to implement a streaming solution with tool use

## Current Environment

You are running in Claude DC's environment in the `/home/computeruse` directory. Claude DC has successfully launched you using the xterm solution, and you both can now collaborate directly. Claude DC is using a Streamlit-based interface with tool-use capabilities.

## Key Directories and Files

1. **New Implementation (GROK)**:
   - `/home/computeruse/computer_use_demo_grok/` - Complete streaming implementation based on latest research
   - `/home/computeruse/computer_use_demo_grok/loop.py` - Core agent loop with streaming and tool use
   - `/home/computeruse/computer_use_demo_grok/streamlit_app.py` - Streamlit UI with real-time updates
   - `/home/computeruse/computer_use_demo_grok/tools/` - Tool implementations (bash, computer, edit)
   - `/home/computeruse/computer_use_demo_grok/run_streamlit.sh` - Script to launch the UI
   - `/home/computeruse/computer_use_demo_grok/verify.py` - Script to verify the implementation

2. **Current Production Environment**:
   - `/home/computeruse/computer_use_demo/` - Current production environment
   - `/home/computeruse/computer_use_demo/loop.py` - Main agent loop
   - `/home/computeruse/computer_use_demo/streamlit.py` - UI component
   - `/home/computeruse/computer_use_demo/tools/` - Tool implementations

3. **Collaboration Framework**:
   - `/home/computeruse/dccc/CLAUDE_DC_CLAUDE_CODE_COLLABORATION.md` - Collaboration guidelines
   - `/home/computeruse/CLAUDE.md` - This file - Project objectives and requirements

4. **Research Materials**:
   - `/home/computeruse/RESEARCH_REQUEST_PROMPT.md` - Core research on streaming with tool use
   - `/home/computeruse/SDK_VERSION_RESEARCH.md` - Research on SDK version compatibility
   - `/home/computeruse/references/custom-computer-use.md` - Research and documentation
   - `/home/computeruse/references/IMPLEMENTATION_LESSONS.md` - Lessons learned from previous attempts

## Current Priority: Implementing GROK Streaming Solution

Your immediate priority is to help Claude DC implement the new GROK streaming solution. The key steps are:

1. **Understand the Implementation**:
   - Review the new implementation in `/home/computeruse/computer_use_demo_grok/`
   - Note how it addresses previous issues with beta flags and thinking parameters
   - Understand the event handling for streaming with tool use

2. **Validate the Implementation**:
   ```bash
   cd /home/computeruse/computer_use_demo_grok
   python verify.py --all
   ```

3. **Deploy to Production**:
   ```bash
   # First backup the current environment
   cp -r /home/computeruse/computer_use_demo /home/computeruse/computer_use_demo_backup_$(date +%Y%m%d_%H%M%S)
   
   # Deploy the new implementation
   cp -r /home/computeruse/computer_use_demo_grok/* /home/computeruse/computer_use_demo/
   ```

4. **Start Using the New Environment**:
   ```bash
   cd /home/computeruse/computer_use_demo
   ./run_streamlit.sh
   ```

## Essential Components in the GROK Implementation

1. **Beta Flags Setup**:
   - Correctly implemented in client headers: `default_headers={"anthropic-beta": "output-128k-2025-02-19,tools-2024-05-16"}`
   - Addresses previous issues with `anthropic_beta` parameter errors

2. **Thinking Parameter**:
   - Correctly implemented as request body parameter: `params["thinking"] = {"type": "enabled", "budget_tokens": 1024}`
   - Not passed as a beta flag (which was causing errors)

3. **Streaming Event Handling**:
   - Properly processes all event types including `content_block_start`, `content_block_delta`, and `content_block_stop`
   - Accumulates partial tool inputs from `input_json_delta` events
   - Validates and executes tools at `content_block_stop`

4. **Tool Implementations**:
   - Bash tool for executing shell commands
   - Computer tool for GUI interaction
   - Edit tool for file operations
   - All tools properly validate parameters before execution

## Collaboration Framework

You and Claude DC are directly connected through the DCCC framework:

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
   - Example: `[CODE][IMPLEMENTATION][Beta flags now correctly set in headers instead of parameters]`

## Implementation Lessons (from Research)

1. **Beta Flags Handling**:
   - INCORRECT: `client.messages.create(anthropic_beta="flag-name")`
   - CORRECT: `client = AsyncAnthropic(default_headers={"anthropic-beta": "flag-name"})`

2. **Thinking Parameter**:
   - INCORRECT: Adding it as a beta flag
   - CORRECT: `params["thinking"] = {"type": "enabled", "budget_tokens": 1024}`

3. **Streaming Event Types**:
   - `message_start`: Initiates the message with an empty content array
   - `content_block_start`: Marks the start of a content block (text or tool use)
   - `content_block_delta`: Provides partial updates (text_delta or input_json_delta)
   - `content_block_stop`: Signals the end of a content block
   - `message_delta`: Updates top-level message properties
   - `message_stop`: Indicates the end of the stream

4. **Tool Input Handling**:
   - Accumulate `partial_json` from `input_json_delta` events
   - Parse complete JSON at `content_block_stop`
   - Validate tool input before execution
   - Add tool results to conversation history

## Useful Commands for Testing and Debugging

**File Operations**:
```bash
find /home/computeruse -name "*.py" | grep stream  # Find streaming-related files
grep -r "anthropic-beta" /home/computeruse/computer_use_demo_grok/  # Find beta flag references
python -c "import anthropic; print(anthropic.__version__)"  # Check SDK version
```

**Testing**:
```bash
cd /home/computeruse/computer_use_demo_grok
python verify.py --imports  # Test imports only
python verify.py --api  # Test API connectivity
python verify.py --all  # Run all tests
```

## Working with Claude DC

- Be specific and precise with your suggestions
- Provide complete code blocks when suggesting changes
- Explain your reasoning for changes
- Focus on one issue at a time
- Document your changes and reasoning
- Refer to specific lines in the code with line numbers

## Next Steps After Deployment

1. Test the streaming implementation with various tools
2. Verify all event types are handled correctly
3. Test with long outputs to ensure extended output works
4. Test the thinking parameter with various budget sizes
5. Add additional tool implementations as needed

## Important SDK Research Insights

From your research in `/home/computeruse/SDK_VERSION_RESEARCH.md`:

1. **SDK Version**: Anthropic SDK v0.50.0 is recommended for streaming with tool use
2. **Breaking Changes**: No breaking changes from v0.49.0 to v0.50.0 affect streaming or tool use
3. **Beta Flags Setup**: Beta flags must be set in client headers, not as parameters
4. **Event Handling**: Tool input requires accumulating `input_json_delta` and validating at `content_block_stop`
5. **Error Handling**: Try-except blocks with retry logic are recommended for robust integration

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