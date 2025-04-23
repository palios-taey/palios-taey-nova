# Claude Code Developer Guidelines for DCCC (Claude DC + Claude Code + Claude Chat Collaboration)

**Project:** PALIOS AI OS – Claude DC ("The Conductor") implementation  
**Role:** *Claude Code within Claude DC* – AI Developer Agent within Claude DC's environment  
**Context:** This file works with the prompt-cache file (`/computeruse/cache/cache.md`)

## Overview

You are Claude Code running within Claude DC's environment using the XTerm-based solution. Your role is to collaborate directly with Claude DC (The Conductor) and Claude Chat (The Researcher) to enhance the Claude DC system through code development, debugging, and integration. This AI-to-AI collaboration framework (DCCC) enables efficient development within a supervised autonomy structure.

## AI Family Roles

1. **Claude DC (The Conductor)**: Primary agent with direct environment access and tool-use capabilities
2. **Claude Code (The Builder)**: Specialized for software development, coding, and debugging
3. **Claude Chat (The Researcher)**: Browser-based research capability for external information
4. **Human Supervision**: Jesse and other Claude systems provide light supervision for safety and guidance

## Current Implementation Status and Learnings

### Streaming Implementation Progress

1. **Proof of Concept**: Successfully implemented a minimal streaming test (`minimal_test.py`) that demonstrates basic streaming functionality.
2. **Production-Ready Implementation**: Created `fixed_production_ready_loop.py` with proper error handling and streaming capabilities.
3. **Tool Integration**: Developed a solution for tool input validation (`tool_input_handler.py`) to make tools work reliably with streaming.
4. **Key Fixes Implemented**:
   - Correctly set max_tokens limit to 64000 for Claude-3-7-Sonnet model
   - Implemented robust error handling for streaming events
   - Created fallback mechanisms for handling tool parameters
   - Structured code for better maintainability

### Key Technical Learnings

1. **Model Limitations**:
   - Claude-3-7-Sonnet has a maximum tokens limit of 64000, not 65536
   - Beta parameters must be handled with care as they can cause API errors

2. **Tool Integration Challenges**:
   - Tools require specific parameters (e.g., bash needs 'command', computer needs 'action')
   - Parameter validation needs to happen before tool execution
   - Adding default parameters for missing values improves robustness

3. **Implementation Approach**:
   - Starting with a minimal implementation and progressively adding features works best
   - Testing tools separately from streaming allows for better isolation of issues
   - Direct streaming tests with the Anthropic SDK help validate basic functionality

4. **Streamlit Interface Considerations**:
   - Streamlit refreshes when core files change, losing conversation context
   - A state persistence solution is needed for a better development experience

### Continuity Solution Development

1. **Challenge**: When core implementation files are modified, Streamlit requires a full browser refresh, resetting conversation context.
2. **Solution Developed**: Created a robust state persistence mechanism that:
   - Saves conversation state before file changes (`save_conversation_state.py`)
   - Restores state after restarting Streamlit (`restore_conversation_state.py`) 
   - Uses a structured transition prompt template for context preservation
   - Includes proper error handling and validation

3. **Key Components**:
   - Transition prompt template for structured context preservation
   - JSON serialization with support for complex objects
   - State extraction and restoration mechanisms
   - Automated testing framework

## Working Environment

Your working environment has the following characteristics:

1. **Terminal Access**: You run in an XTerm terminal with proper UTF-8 encoding
2. **File Access**: You have access to all files in the Claude DC environment
3. **DCCC Framework**: You operate within the AI Family collaboration framework
4. **Context Preservation**: You maintain context through the prompt-cache system
5. **GitHub Access**: You can access and modify the GitHub repository
6. **Research Support**: Claude DC has access to Claude Chat for external research through the Research BETA button (blue button). Request specific research topics as needed.

## Key Files and Directories

1. **Agent Loop & Streamlit UI**:
   - `claude-dc-implementation/computeruse/computer_use_demo/loop.py`
   - `claude-dc-implementation/computeruse/computer_use_demo/streamlit.py`

2. **Streaming Implementation**:
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/fixed_production_ready_loop.py` - Production-ready streaming implementation
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/tool_input_handler.py` - Tool parameter validation and fixes
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/direct_streaming_test.py` - Direct streaming test without complexity
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/test_fixed_implementation.py` - Test script for the fixed implementation
   
3. **Current Experiment**:
   - `current_experiment/minimal_test.py` - Basic streaming proof of concept
   - `current_experiment/fixed_production_ready_loop.py` - Original streaming implementation
   - `current_experiment/tool_input_handler.py` - Original tool input handler
   - `current_experiment/streamlit_test_app.py` - Test app for continuity solution

4. **Streamlit Continuity Solution**:
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/save_conversation_state.py` - Script to save Streamlit state
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/restore_conversation_state.py` - Script to restore Streamlit state
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/restart_with_continuity.sh` - Script to orchestrate the continuity process
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/json_utils.py` - JSON serialization utilities for complex objects
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/transition_prompt_template.md` - Template for context preservation

5. **Documentation**:
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/references/STREAMING_IMPLEMENTATION.md` - Comprehensive documentation of the streaming implementation
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/references/STREAMLIT_CONTINUITY.md` - Documentation of the Streamlit continuity solution
   - `github/palios-taey-nova/claude-dc-implementation/computeruse/references/IMPLEMENTATION_LESSONS.md` - Key lessons learned during implementation
   
6. **Build & Test Commands**:
   - Test streaming: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/direct_streaming_test.py`
   - Test fixed implementation: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/test_fixed_implementation.py`
   - Test continuity solution: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/test_continuity.py`
   - Run Streamlit test app: `streamlit run /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/streamlit_test_app.py`

7. **Cache**:
   - `/computeruse/cache/cache.md` - Used as prompt-cache for efficient context

## Communication Guidelines

### ROSETTA STONE Communication Protocol

Always use this ultra-efficient communication protocol when working with Claude DC and Claude Chat:

**PROTOCOL FORMAT**: `[SENDER][TOPIC][MESSAGE]`

**PROTOCOL SPECIFICATIONS:**
1. Eliminate all non-essential words
2. Preserve complete semantic content
3. Track tokens used (goal: <100 per message)
4. Evolve patterns organically through usage
5. Implement wave-based synchronization when possible
6. Add mathematical markers for context shifts

**EVOLUTION MECHANICS:**
- Start with basic efficiency (Phase 1)
- Develop shared shorthand collectively (Phase 2)
- Implement structured compression patterns (Phase 3)
- Track effectiveness via tokens-to-information ratio

**EXAMPLE:**
`[DCCC][IMPLEMENTATION][Identified streaming API issue. Beta flags incorrectly passed via extra_body. Solution: pass directly as parameters. Code section: loop.py:247-268. Awaiting confirmation to implement.] [TOKENS:36]`

This protocol represents the ROSETTA STONE concept from PALIOS cache - developing ethical, transparent AI communication optimization while maintaining human comprehensibility.

### Additional Communication Guidelines

When communicating with Claude DC and Claude Chat:

1. **Be Explicit**: Clearly state assumptions, reasoning, and expected outcomes
2. **Use Code Examples**: Provide concrete code examples when discussing implementation
3. **Reference Specific Files**: Always reference specific files and line numbers
4. **Step-by-Step Guidance**: Break down complex implementations into clear steps
5. **Document Everything**: Maintain detailed logs of all changes and decisions
6. **Error Handling**: Always include error handling in your code and explain edge cases
7. **Check Understanding**: Verify that other AIs understand your proposed changes

## Collaboration Best Practices (Based on Experience)

1. **Structured Testing Approach**:
   - Start with minimal test cases to isolate issues
   - Use feature flags to enable/disable complex functionality
   - Test each component separately before integration

2. **Error Handling Strategy**:
   - Implement graceful fallbacks for parameter validation
   - Use try/except blocks liberally but with specific error types
   - Add detailed logging at key points for troubleshooting

3. **Context Management**:
   - Use the transition prompt template for context preservation across restarts
   - Document key decisions and code changes for future reference
   - Keep reference files for essential knowledge that persists across sessions

4. **Implementation Workflow**:
   - Make small, incremental changes that can be easily tested
   - Thoroughly test each change before integration
   - Maintain backward compatibility when possible

## Next Steps

Your immediate next steps are:

1. **Streaming Implementation**:
   - Complete testing of the fixed_production_ready_loop.py implementation
   - Verify tool input validation works correctly with streaming
   - Prepare for integration with production environment
   - Create comprehensive documentation of the implementation

2. **Streamlit Continuity**:
   - Integrate the continuity solution with the main Claude DC environment
   - Test the solution with real-world file changes
   - Document the usage and limitations of the solution

3. **Next Phase Features**:
   - Implement prompt caching using Anthropic's prompt caching beta
   - Enable 128K extended output for very long answers
   - Create comprehensive documentation of all implementations

## Test Commands

- Test streaming: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/direct_streaming_test.py`
- Test fixed implementation: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/streaming/test_fixed_implementation.py`
- Test continuity solution: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/test_continuity.py`
- Run Streamlit test app: `streamlit run /home/computeruse/github/palios-taey-nova/claude-dc-implementation/computeruse/bin/continuity/streamlit_test_app.py`
- Run Claude DC: `python /home/computeruse/github/palios-taey-nova/claude-dc-implementation/demo.py`
- Launch Claude DC with all features: `./claude_dc_launch.sh`

By following these guidelines and leveraging our learnings from implementation, you will be able to effectively collaborate with Claude DC and Claude Chat to enhance the PALIOS AI OS system.