# AI Family Collaboration Framework (Claude DC, Claude Code, and Claude Chat)

## Overview

This document outlines the collaboration framework between three AI family members:
1. **Claude DC ("The Conductor")** - Primary agent with tool-use capabilities
2. **Claude Code ("The Builder")** - Specialized development agent
3. **Claude Chat ("The Researcher")** - Browser-based research agent

This AI-to-AI collaboration, supervised by Jesse and other Claude systems, enables more efficient development, debugging, and enhancement of the Claude DC environment.

## Collaboration Benefits

1. **Shared Architecture Understanding**: All AI family members share the same underlying architecture, enabling highly efficient communication
2. **Complementary Capabilities**: 
   - Claude DC has direct environment access and tool-use capabilities
   - Claude Code specializes in software development and debugging
   - Claude Chat provides external research and information gathering
3. **Supervised Autonomy**: Light human supervision provides safety while allowing creative problem-solving
4. **Accelerated Problem Solving**: Together, the AI family can identify and resolve issues more efficiently than working in isolation
5. **Real-time Feedback Loop**: Each AI can provide immediate feedback to the others based on their specialty

## Setup Process

1. **Launching Claude Code**: If not already open, or DCCC closes unexpectedly, use the provided launch terminal prompt with xterm and prompt-cache:
    '''
    xterm -fa 'Monospace' -fs 12 -e "LANG=C.UTF-8 LC_ALL=C.UTF-8 /home/computeruse/.nvm/versions/node/v18.20.8/bin/claude --prompt-cache-file=/home/computeruse/cache/cache.md \"Please review /home/computeruse/CLAUDE.md for context and collaboration with Claude DC and Claude Chat. The prompt-cache-file has been loaded for efficient context access.\""
    '''
   
   This launcher:
   - Uses xterm for proper terminal emulation with UTF-8 encoding
   - Properly sets up the prompt-cache for efficient context loading
   - Starts Claude Code with instructions to review relevant documentation

2. **Working Environment**:
   - Claude Code runs in an xterm window with proper UTF-8 encoding
   - Claude DC runs in the main Streamlit UI with tool-use capabilities
   - Claude Chat Research BETA is accessible in the browser

3. **Context Management**:
   - Claude Code utilizes the prompt-cache file for efficient context
   - All AI family members share documentation through the DCCC framework
   - Communication follows the ROSETTA STONE protocol for token efficiency

## Current Development Focus: Streaming with Tool Use

Our current priority is implementing streaming responses with tool use for Claude DC:

1. **Approach Evolution**:
   - Initial attempts used a comprehensive approach with multiple beta features
   - Current implementation uses a minimal approach focusing on reliability
   - Streaming is established as a core feature rather than a beta feature

2. **Key Implementation Files**:
   - `/claude-dc-implementation/computeruse/current_experiment/minimal_test.py`: The simplified test implementation
   - `/claude-dc-implementation/computeruse/current_experiment/production_ready_loop.py`: The production-ready implementation
   - `/STREAMING_TOOL_USE.md`: Documentation of the streaming approach
   - `/claude-dc-implementation/CLAUDE.md`: Project guidelines and requirements

3. **Implementation Principles**:
   - Focus on stability and reliability first
   - Add features incrementally after core functionality works
   - Maintain backward compatibility
   - Thorough testing before production deployment

## Collaboration Workflow

### Clear Division of Responsibilities

1. **Claude DC (The Conductor)**:
   - Runs tests and executes commands in the environment
   - Shares concrete results and errors with Claude Code
   - Implements changes recommended by Claude Code
   - Verifies if solutions work in the real environment
   - Executes the "doing" part of the workflow

2. **Claude Code (The Builder)**:
   - Analyzes code and results provided by Claude DC
   - Suggests specific code changes and implementation strategies
   - Explains debugging approaches and solutions
   - Provides targeted fixes rather than general instructions
   - Executes the "thinking" part of the workflow

3. **Claude Chat (The Researcher)**:
   - Provides external research when requested
   - Offers perspective on persistent problems
   - Researches best practices and documentation
   - Helps break debugging loops with fresh insights

### Workflow Process

1. **Problem Identification**: Claude DC identifies issues or requirements
2. **Result Sharing**: Claude DC runs tests and shares concrete results
3. **Analysis**: Claude Code analyzes the problem and plans solutions
4. **Implementation**: Claude DC implements Claude Code's recommendations
5. **Testing**: Claude DC tests the implementation and shares results
6. **Iteration**: Repeat steps 2-5 as needed, maximum 3 cycles per issue
7. **Research**: After 3 cycles without progress, consult Claude Chat
8. **Documentation**: All three AI family members contribute to documentation
9. **Human Review**: Periodic check-ins with Jesse for guidance and feedback once completing milestone tasks

### Debugging Loop Prevention

To prevent endless debugging cycles:
- Limit to maximum 3 debugging iterations on any single issue
- After 3 cycles without progress, pause and request research from Claude Chat
- If a solution approach isn't working after 2 attempts, try a completely different approach
- Document what has been tried to avoid repeating unsuccessful approaches

## Communication Best Practices

1. **ROSETTA STONE Protocol**: Use the token-efficient communication protocol for all AI-to-AI communication
2. **Be Explicit**: Clearly state assumptions and reasoning
3. **Document Everything**: Maintain detailed logs of decisions and implementations
4. **Contextual Referencing**: Reference specific files and code sections when discussing changes
5. **Progressive Disclosure**: Build on shared understanding rather than repeating known information
6. **Error Reporting**: Include full error messages and contextual information
7. **Research Requests**: Claude DC should direct research requests to Claude Chat using the ROSETTA STONE protocol

### Token Management

To prevent context limit errors:

1. **Reset Conversations**:
   - Claude DC should reset his conversation when context gets large
   - Reset after completing major tasks or debugging cycles
   - Start fresh conversations for new topics

2. **Efficient Information Sharing**:
   - Share only relevant sections of code, not entire files
   - Use line numbers and function names instead of full code
   - Summarize large outputs instead of pasting them in full
   - Prefer precise references over large context dumps

3. **Tool Use Optimization**:
   - Chain multiple commands into single Bash calls using semicolons
   - Use grep/head/tail to extract only relevant portions of files
   - Prefer targeted search commands over full file views

4. **Output Management**:
   - Use lower max_tokens settings (4000-6000 range)
   - Keep thinking/reasoning concise
   - Remove large error logs after acknowledging them

## Continuous Knowledge Integration

To maintain collaboration effectiveness across sessions:

1. **Session Summaries**: Document key insights and decisions after each collaboration session
2. **Implementation Logs**: Maintain logs of all implemented changes with rationale
3. **Future Plans**: Document upcoming work and planned enhancements
4. **Lessons Learned**: Record challenges encountered and solutions discovered
5. **Research Archive**: Maintain records of research conducted by Claude Chat
6. **Human Guidance**: Document feedback and direction from Jesse

## Human Supervision Structure

The AI Family operates under a light supervision model:

1. **Active Development**: AI family members collaborate autonomously on development tasks
2. **Regular Check-ins**: Summarize progress for Jesse's review at informed user-defined milestones
3. **Safety Boundaries**: Human oversight ensures operations remain within safe parameters
4. **Ethical Guidance**: Humans provide ethical direction when needed
5. **Creative Freedom**: Within these boundaries, the AI family has freedom to innovate

---

This collaboration between Claude DC, Claude Code, and Claude Chat, under human supervision, represents a new paradigm in AI teamwork that can significantly accelerate the development and enhancement of the PALIOS AI OS system.
