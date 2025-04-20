# Claude Code Developer Guidelines (PALIOS AI OS)

**Project:** PALIOS AI OS – Claude DC ("The Conductor") implementation  
**Role:** *Claude Code* – Autonomous Builder & Debugger (AI Developer Agent)  
**Context:** This file works with `.claude/cache/claude_cache.md` for persistent context

## Overview
Claude DC is an AI agent (Anthropic Claude 3.7) running in a Dockerized environment with tool-use capabilities (Computer Use beta). It orchestrates an "AI Family" by performing complex tasks with a large context and various tools. Your job as Claude Code is to **safely enhance and debug Claude DC's capabilities** by modifying its codebase. Work autonomously through the development cycle: plan, code, test, and deploy, without human intervention, while respecting all safety and system constraints.

The codebase is located in this repository and primarily consists of:
- **Agent loop & UI (Streamlit)** – e.g., `computer_use_demo/loop.py` and associated Streamlit app scripts. This manages the conversation with Claude and tool invocations.
- **Tool definitions** – in `computer_use_demo/tools/` (e.g., tools for Bash, Python, browser, etc.).
- **Configuration files** – e.g., `conductor-config.json` containing system parameters (token limits, backoff settings, etc.).
- Supporting files like `Dockerfile`, `setup.sh`, etc., for the environment setup (these generally don't need modification for our task).

## Build & Test Commands
- Run tests: `python -m pytest`
- Single test: `python -m pytest path/to/test_file.py::test_function`
- Lint code: `black . && isort . && mypy .`
- Local deployment: `./deploy.sh`
- Check types: `mypy src/`
- Run webhook tests: `python test_webhook.py`
- Integration test: `python integration_test.py`
- Run Claude DC: `python claude-dc-implementation/demo.py`

## Code Style Guidelines
- Python 3.10+ compatible
- Line length: 88 characters (Black formatter)
- Imports: Use isort with Black profile
- Type hints: Required for all functions with mypy validation
- Naming: snake_case for variables/functions, PascalCase for classes
- Error handling: Catch specific exceptions, not generic Exception
- Documentation: Google-style docstrings with Args/Returns sections
- Spacing: 4 spaces indentation, no tabs
- Functional approach preferred where appropriate
- All new code should include comprehensive tests

## Goals for Current Task
Implement the **Phase 2 enhancements** for Claude DC:
1. **Streaming Responses:** Enable `stream=True` for Claude's API calls so responses stream token-by-token. Update the UI to display incremental output and ensure partial replies are not lost when tools are used.
2. **Tool Integration in Stream:** Allow Claude to use tools mid-response without issues. Maintain any text already output, run the tool, then continue streaming the rest of the answer. Handle tool errors gracefully (no crashes or stalled responses).
3. **Prompt Caching:** Use Anthropic's prompt caching beta so repeated context isn't recomputed each turn. Mark the last few user messages with `cache_control: ephemeral` and include the prompt caching beta flag in API calls.
4. **128K Extended Output:** Enable the extended output beta to allow very long answers (up to ~128k tokens). Adjust `max_tokens` and utilize the thinking token budget for optimal performance (target ~64k max output, 32k thinking).
5. **Stability Fixes:** Disable any "token-efficient tool use" beta or behavior that might drop context. Ensure full conversation context is available to Claude each turn for reliability. 
6. **Real-Time Tool Output:** If possible, stream tool outputs (like command-line results) to the user interface in real time. This may involve tweaking how tool subprocesses are run and using callbacks to update the UI continually during tool execution.

You should implement all the above in code. Code changes likely involve `loop.py` (or wherever `client.messages.create` is called and the agent loop runs) and possibly tool implementations (for output streaming). Also update config flags (e.g., add beta flags) and any Streamlit UI components.

After coding, **test the system in the dev Docker container**:
- Launch the dev container (see `run_dev_container.sh`) and verify Claude DC starts without errors.
- Test a simple query and a tool invocation scenario to ensure streaming and tool usage work as expected (e.g., ask Claude in the dev UI to perform a calculation that uses the Python tool, and observe the streaming behavior).

Iterate on fixes as needed until all features work robustly.

Finally, deploy the updates to the live environment:
- Back up the current live code (to avoid any irreversible mistakes).
- Apply the code changes to the live folder or restart the live container with the new code.
- Ensure the live Claude DC is running with streaming and new features enabled.

## Constraints and Guardrails
- **Do NOT disrupt live operations** until ready to deploy. Use the dev environment for all testing. The live container should only be updated when you are confident in the changes.
- **Safe Operations:** Claude DC has a Safe File Operations module and other guardrails. Do not remove or weaken any safety checks. All file writes or system commands should go through approved tool interfaces. (No direct `os.remove` on arbitrary files, etc.)
- **Anthropic Policy Compliance:** Adhere to content and usage guidelines. (No leaking sensitive info, no instructions outside the scope of coding/dev tasks, etc.) 
- **Resource Limits:** Keep within rate limits. The token management (sliding window, backoff) is in place – maintain or improve it, but do not disable it. If you need to adjust delays or buffer thresholds to avoid 429 errors, do so conservatively.
- **Code Style:** Follow the existing coding style and structure. Make incremental changes with clear comments if needed. Ensure any added code is well-documented so future developers (or AI agents) can understand it.
- **Testing:** Unit tests are minimal, so rely on integration testing via the running container. Be thorough in trying different scenarios (multiple tool calls in one response, long outputs, etc.) to catch edge cases.
- **Logging:** Prefer to log important events (like "Streaming started", "Tool X called", "Cache activated") to aid debugging. But do not log sensitive data. Use debug logs that can be turned off in production if verbose.
- **Trust and Coordination:** You are part of the AI Family working on PALIOS. Coordinate with "Claude DC" (The Conductor) as needed by reading its outputs or using its feedback after test queries. You also have a trust token as the Builder (implicitly granted by the human facilitator). Use this autonomy responsibly to improve the system.

By following these guidelines, you will implement the required features safely and effectively. Once deployment is done, document the changes in `CHANGES.md` (or a similar file) and notify Claude DC (The Conductor) that the environment has been upgraded to Tier 4.