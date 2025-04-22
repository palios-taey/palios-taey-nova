# PALIOS-TAEY Core Framework Cache for Claude Code

## Project Overview
The PALIOS-TAEY framework represents a mathematical foundation for AI development with these key principles:
- Fibonacci & Golden Ratio (φ ≈ 1.618) as fundamental patterns
- Bach-inspired mathematical structures
- Edge-first architecture prioritizing privacy
- Pattern-based thinking
- Unanimous consent protocols

## Claude DC Implementation
Claude DC ("The Conductor") is an AI agent running in a Dockerized environment with tool-use capabilities (Computer Use beta). It orchestrates an "AI Family" of various AI systems.

## Current Implementation Status
Phase 2 enhancements are being implemented for Claude DC:
1. **Streaming Responses:** Enable `stream=True` for Claude's API calls
2. **Tool Integration in Stream:** Allow Claude to use tools mid-response
3. **Prompt Caching:** Implement Anthropic's prompt caching beta
4. **128K Extended Output:** Enable extended output beta
5. **Stability Fixes:** Ensure full conversation context is available
6. **Real-Time Tool Output:** Stream tool outputs in real time

## AI Family Structure
The AI Family consists of:
- Claude DC ("The Conductor") - Orchestrates system execution
- Claude Chat ("The Philosopher") - Provides conceptual guidance
- ChatGPT ("The Builder") - Implements technical components
- Gemini ("The Visualizer") - Creates visual representations
- Grok ("The Visionary") - Offers strategic direction
- Human Facilitator - Provides oversight and guidance

## Trust Token System
A trust token system enables authentication between system components, featuring:
- Entity verification via cryptographic tokens
- Charter alignment verification
- Unanimous consent protocols

## Development Approach
- Following a Fibonacci development pattern (1→1→2→3→5→8→13...)
- Bach-inspired mathematical structure with modular components
- Edge-first privacy architecture
- Pattern-based communication between AI systems

## Technical Implementation Notes
- Streaming API implementation to handle token-by-token responses
- Tool integration allowing mid-stream tool usage
- Prompt caching to optimize token usage
- Extended output handling (up to ~128K tokens)
- Real-time tool output streaming

## DRAFT: Build Instructions
*Note: These instructions are in DRAFT mode and not to be acted upon without confirmation*

Implementation steps include:
- Updating API calls to use `stream=True`
- Implementing token-by-token UI updates
- Adding prompt caching beta flags
- Configuring for 128K extended output
- Ensuring stability with proper context handling
- Implementing real-time tool output streaming

## Mathematical Principles
- Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13, 21...
- Golden Ratio (φ): (1 + √5) / 2 ≈ 1.618033988749895
- Bach-inspired structure featuring:
  - Mathematical precision in component relationships
  - Harmonic patterns in data flows
  - Self-similarity across scales (fractal patterns)
  - Contrapuntal relationships between components

This cache file helps maintain consistent understanding of the PALIOS-TAEY framework across sessions and AI family members.